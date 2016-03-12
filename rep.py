import requests
import json
import pprint
import sys
import sqlite3
import os
import argparse
import ConfigParser
import cherrypy

class Rep():
    def __init__(self, args):

        config = ConfigParser.ConfigParser()
        config.read("gh-rep.conf")

        client_id = config.get("auth", "client_id")
        client_secret = config.get("auth", "client_secret")

        #client_id = args.i
        #client_secret = args.s

        self.repo_people = None
        self.repo_events = None
        self.db = None

        self.repourl = "https://api.github.com/repos/" + str(args.r)
        self.reponame = self.repourl[29:].lower()
        self.user = 'https://api.github.com/users/jonobacon'
        self.auth = "client_id=" + client_id + "&client_secret=" + client_secret

        self.setup_db()
        self.scan_api()

    def setup_db(self):
        """Remove a pre-existing database and create a new database and schema."""

        if os.path.isfile("db.sql"):
            os.remove("db.sql")

        print "Setting up the database..."
        self.db = sqlite3.connect("db.sql", check_same_thread=False)

        # users
        self.db.execute("CREATE TABLE users (ID INTEGER PRIMARY KEY, \
            USERNAME TEXT NOT NULL, \
            AVATAR_URL TEXT NOT NULL \
            )")

        # repoevents
        self.db.execute("CREATE TABLE reposcores (ID INTEGER PRIMARY KEY, \
            REPO TEXT NOT NULL, \
            EVENT TEXT NOT NULL, \
            SCORE INT NOT NULL \
            )")

        # reputation
        self.db.execute("CREATE TABLE events (ID INTEGER PRIMARY KEY, \
            USER INT NOT NULL, \
            REPOEVENT INT NOT NULL, \
            DATECREATED DATETIME NOT NULL, \
            REP INT NOT NULL, \
            FOREIGN KEY(USER) REFERENCES users(ID), \
            FOREIGN KEY(REPOEVENT) REFERENCES repoevents(ID) \
            )")

        print "...done."

    def scan_api(self):
        """Scan the API for data and return people and events"""
        data = {}

        data_repo = requests.get(self.repourl + "?" + self.auth)
        data_repo_json = json.loads(data_repo.text or data_repo.content)

        data_events = requests.get(self.repourl + "/events?" + self.auth + "&per_page=100")
        data_events_json = json.loads(data_events.text or data_events.content)

        if 'Link' in data_events.headers.keys():
            num_pages = data_events.links["last"]["url"].split("&page=")[-1]
        else:
            num_pages = 1

        people = { }
        events_data = []

        if num_pages == 1:
            d_page = requests.get(self.repourl + "/events?" + self.auth + "&per_page=100")
            d_page_json = json.loads(d_page.text or d_page.content)
        else:
            for i in range(1, int(num_pages)+1):
                d_page = requests.get(self.repourl + "/events?" + self.auth + "&page=" + str(i) + "&per_page=100")
                d_page_json = json.loads(d_page.text or d_page.content)

                for event in d_page_json:
                    people[event["actor"]["login"]] = event["actor"]["avatar_url"]
                    events_data.append(event)

        self.repo_people = people
        self.repo_events = events_data

        self.populate_db(self.repo_people)

    def populate_db(self, people):
        """Populate a new DB with data"""

        print people

        # Add users to DB
        users = {}
        key = 1
        for user in set(people):
            print user
            sql = "INSERT INTO users(USERNAME, AVATAR_URL) VALUES('" + str(user) + "', '" + str(people[user]) + "')"
            users[user] = key
            self.db.execute(sql)
            self.db.commit()
            key = key + 1

        # Pre-defined events and scores
        events = {}
        events["CommitCommentEvent"] = 60
        events["CreateEvent"] = 30
        events["DeleteEvent"] = 30
        events["DeploymentEvent"] = 0
        events["DeploymentStatusEvent"] = 0
        events["DownloadEvent"] = 0
        events["FollowEvent"] = 0
        events["ForkEvent"] = 20
        events["ForkApplyEvent"] = 0
        events["GistEvent"] = 0
        events["GollumEvent"] = 30
        events["IssueCommentEvent"] = 50
        events["IssuesEvent"] = 20
        events["MemberEvent"] = 0
        events["MembershipEvent"] = 0
        events["PageBuildEvent"] = 0
        events["PublicEvent"] = 100
        events["PullRequestEvent"] = 100
        events["PullRequestReviewCommentEvent"] = 80
        events["PushEvent"] = 80
        events["ReleaseEvent"] = 100
        events["RepositoryEvent"] = 0
        events["StatusEvent"] = 0
        events["TeamAddEvent"] = 0
        events["WatchEvent"] = 1

        # Add events for the repo
        reposcores = {}
        key = 1
        for k, v in events.items():
            sql = "INSERT INTO reposcores(REPO, EVENT, SCORE) VALUES('" + str(self.reponame) + "', '" + k + "', " + str(v) + ")"
            self.db.execute(sql)
            reposcores[k] = key
            key = key + 1

        self.db.commit()

        # Add repo activity to the DB
        print "Processing events:"
        for event in self.repo_events:
            self.process_event(event)
        print "done."

    def process_event(self, event):
        """Process an individual event from the API"""

        rep = 0
        cursor = self.db.execute("SELECT ID, SCORE FROM reposcores WHERE EVENT = '" + event["type"] + "'")
        repo_event_id, repo_score = [record for record in cursor.fetchall()][0]

        usercursor = self.db.execute("SELECT ID FROM users WHERE USERNAME = '" + event["actor"]["login"] + "'")
        user_id = [str(record[0]) for record in usercursor.fetchall()][0]

        created_at_date = event["created_at"][:10] + " " + event["created_at"][-9:-4]

        # Apply any filtering to the different event types to tune the score
        if event["type"] == "CommitCommentEvent":
            rep = self.process_event_CommitCommentEvent(event, repo_score)

        elif event["type"] == "CreateEvent":
            rep = self.process_event_CreateEvent(event, repo_score)

        elif event["type"] == "DeleteEvent":
            rep = self.process_event_DeleteEvent(event, repo_score)

        elif event["type"] == "DeploymentEvent":
            rep = self.process_event_DeploymentEvent(event, repo_score)

        elif event["type"] == "DeploymentStatusEvent":
            rep = self.process_event_DeploymentStatusEvent(event, repo_score)

        elif event["type"] == "DownloadEvent":
            rep = self.process_event_DownloadEvent(event, repo_score)

        elif event["type"] == "FollowEvent":
            rep = self.process_event_FollowEvent(event, repo_score)

        elif event["type"] == "ForkEvent":
            rep = self.process_event_ForkEvent(event, repo_score)

        elif event["type"] == "ForkApplyEvent":
            rep = self.process_event_ForkApplyEvent(event, repo_score)

        elif event["type"] == "GistEvent":
            rep = self.process_event_GistEvent(event, repo_score)

        elif event["type"] == "GollumEvent":
            rep = self.process_event_GollumEvent(event, repo_score)

        elif event["type"] == "IssueCommentEvent":
            rep = self.process_event_IssueCommentEvent(event, repo_score)

        elif event["type"] == "IssuesEvent":
            rep = self.process_event_IssuesEvent(event, repo_score)

        elif event["type"] == "MemberEvent":
            rep = self.process_event_MemberEvent(event, repo_score)

        elif event["type"] == "MembershipEvent":
            rep = self.process_event_MembershipEvent(event, repo_score)

        elif event["type"] == "PageBuildEvent":
            rep = self.process_event_PageBuildEvent(event, repo_score)

        elif event["type"] == "PublicEvent":
            rep = self.process_event_PublicEvent(event, repo_score)

        elif event["type"] == "PullRequestEvent":
            rep = self.process_event_PullRequestEvent(event, repo_score)

        elif event["type"] == "PullRequestReviewCommentEvent":
            rep = self.process_event_PullRequestReviewCommentEvent(event, repo_score)

        elif event["type"] == "PushEvent":
            rep = self.process_event_PushEvent(event, repo_score)

        elif event["type"] == "ReleaseEvent":
            rep = self.process_event_ReleaseEvent(event, repo_score)

        elif event["type"] == "RepositoryEvent":
            rep = self.process_event_RepositoryEvent(event, repo_score)

        elif event["type"] == "StatusEvent":
            rep = self.process_event_StatusEvent(event, repo_score)

        elif event["type"] == "TeamAddEvent":
            rep = self.process_event_TeamAddEvent(event, repo_score)

        elif event["type"] == "WatchEvent":
            rep = self.process_event_WatchEvent(event, repo_score)

        # Insert the event into the database

        sql = "INSERT INTO events(USER, REPOEVENT, DATECREATED, REP) VALUES(" + str(user_id) + ", "  + str(repo_event_id) + ", '" + created_at_date + "', " + str(rep) + ")"
        self.db.execute(sql)
        self.db.commit()

        print "...processing: '" + str(event["type"]) + "' (Score: " + str(rep) + ")"

    def process_event_CommitCommentEvent(self, event, repo_score):
        return repo_score

    def process_event_CreateEvent(self, event, repo_score):
        return repo_score

    def process_event_DeleteEvent(self, event, repo_score):
        return repo_score

    def process_event_DeploymentEvent(self, event, repo_score):
        return repo_score

    def process_event_DeploymentStatusEvent(self, event, repo_score):
        return repo_score

    def process_event_DownloadEvent(self, event, repo_score):
        return repo_score

    def process_event_FollowEvent(self, event, repo_score):
        return repo_score

    def process_event_ForkEvent(self, event, repo_score):
        return repo_score

    def process_event_ForkApplyEvent(self, event, repo_score):
        return repo_score

    def process_event_GistEvent(self, event, repo_score):
        return repo_score

    def process_event_GollumEvent(self, event, repo_score):
        return repo_score

    def process_event_CreateEvent(self, event, repo_score):
        return repo_score

    def process_event_IssueCommentEvent(self, event, repo_score):
        rep = 0

        # Check: is this comment a PR comment?
        #  Yes: full points
        #  No: 50% deduction
        if "pull_request" in event["payload"]["issue"]:
            rep = repo_score
        else:
            rep = (repo_score / 2)

        return rep

    def process_event_IssuesEvent(self, event, repo_score):
        rep = 0

        # Check: assess what kind of issue event this is and assign a % of the points
        # for actions that could suggest responsibility and good conduct.
        if event["payload"]["action"] == "assigned":
            rep = (90 * repo_score) / 100
        elif event["payload"]["action"] == "unassigned":
            rep = (90 * repo_score) / 100
        elif event["payload"]["action"] == "labeled":
            rep = (70 * repo_score) / 100
        elif event["payload"]["action"] == "unlabeled":
            rep = (70 * repo_score) / 100
        elif event["payload"]["action"] == "opened":
            rep = (100 * repo_score) / 100
        elif event["payload"]["action"] == "closed":
            rep = (60 * repo_score) / 100
        elif event["payload"]["action"] == "reopened":
            rep = (60 * repo_score) / 100

        return rep

    def process_event_MemberEvent(self, event, repo_score):
        return repo_score

    def process_event_MembershipEvent(self, event, repo_score):
        return repo_score

    def process_event_PageBuildEvent(self, event, repo_score):
        return repo_score

    def process_event_PublicEvent(self, event, repo_score):
        return repo_score

    def process_event_PullRequestEvent(self, event, repo_score):
        rep = 0

        # Check: has the PR been merged?
        #  Yes: full points
        #  No: 50% deduction
        if event["payload"]["pull_request"]["merged_at"] is None:
            rep = repo_score
        else:
            rep = (repo_score / 2)

        return rep

    def process_event_PullRequestReviewCommentEvent(self, event, repo_score):
        return repo_score

    def process_event_PushEvent(self, event, repo_score):
        return repo_score

    def process_event_ReleaseEvent(self, event, repo_score):
        return repo_score

    def process_event_RepositoryEvent(self, event, repo_score):
        return repo_score

    def process_event_StatusEvent(self, event, repo_score):
        return repo_score

    def process_event_TeamAddEvent(self, event, repo_score):
        return repo_score

    def process_event_WatchEvent(self, event, repo_score):
        return repo_score

    @cherrypy.expose
    def index(self):
        html = ""
        head = open("html/header.html", "r")

        html = html + head.read()

        html = html + "<div class='container'><div class='page-header'> \
            <h1>" + self.reponame + " Overview</h1> \
        </div></div> \
        "

        html = html + "<div class='container'><div class='row'>"

        html = html + "<div class='col-sm-4'><h3>Most Active Generalists</h3>"

        # ///// Top Generalists
        sql = "SELECT users.USERNAME, sum(events.REP), users.AVATAR_URL \
                FROM events \
                	JOIN reposcores \
                		ON events.REPOEVENT = reposcores.ID \
                	JOIN users \
                		ON events.USER = users.ID \
                WHERE reposcores.REPO = '" + self.reponame + "' \
                GROUP BY \
                	users.USERNAME \
                ORDER BY 2 DESC \
                LIMIT 10"

        cursor = self.db.execute(sql)

        html = html + "<table class='table'>"

        for row in cursor:
            html = html + "<tr><td><a href='http://www.github.com/" + str(row[0]) + "'><img src='" + str(row[2]) + "' height='25px'> @" + str(row[0]) +  "</a></td><td>" + str(row[1]) + "</td></tr>"

        html = html + "</table></div>"

        # ///// Top in PRs
        html = html + "<div class='col-sm-4'><h3>Most Active in Pull Requests</h3>"
        sql = "SELECT users.USERNAME, sum(events.REP), users.AVATAR_URL \
                FROM events \
                	JOIN reposcores \
                		ON events.REPOEVENT = reposcores.ID \
                	JOIN users \
                		ON events.USER = users.ID \
                WHERE reposcores.REPO = '" + self.reponame + "' \
                	AND reposcores.EVENT = 'PullRequestEvent' \
                	OR reposcores.EVENT = 'PushEvent' \
                    OR reposcores.EVENT = 'CommitCommentEvent' \
                	OR reposcores.EVENT = 'PullRequestReviewCommentEvent' \
                GROUP BY \
                	users.USERNAME \
                ORDER BY 2 DESC \
                LIMIT 10"

        cursor = self.db.execute(sql)

        html = html + "<table class='table'>"

        for row in cursor:
            html = html + "<tr><td><a href='http://www.github.com/" + str(row[0]) + "'><img src='" + str(row[2]) + "' height='25px'> @" + str(row[0]) +  "</a></td><td>" + str(row[1]) + "</td></tr>"

        html = html + "</table></div>"

        # ///// Top in Issues
        html = html + "<div class='col-sm-4'><h3>Most Active in Issues</h3>"
        sql = "SELECT users.USERNAME, sum(events.REP), users.AVATAR_URL \
                FROM events \
                	JOIN reposcores \
                		ON events.REPOEVENT = reposcores.ID \
                	JOIN users \
                		ON events.USER = users.ID \
                WHERE reposcores.REPO = '" + self.reponame + "' \
                	AND reposcores.EVENT = 'IssuesEvent' \
                	OR reposcores.EVENT = 'IssueCommentEvent' \
                GROUP BY \
                	users.USERNAME \
                ORDER BY 2 DESC \
                LIMIT 10"

        cursor = self.db.execute(sql)

        html = html + "<table class='table'>"

        for row in cursor:
            html = html + "<tr><td><a href='http://www.github.com/" + str(row[0]) + "'><img src='" + str(row[2]) + "' height='25px'> @" + str(row[0]) +  "</a></td><td>" + str(row[1]) + "</td></tr>"

        html = html + "</table></div>"

        # ///// Top in Wiki
        html = html + "<div class='col-sm-4'><h3>Most Active in Wiki</h3>"
        sql = "SELECT users.USERNAME, sum(events.REP), users.AVATAR_URL \
                FROM events \
                	JOIN reposcores \
                		ON events.REPOEVENT = reposcores.ID \
                	JOIN users \
                		ON events.USER = users.ID \
                WHERE reposcores.REPO = '" + self.reponame + "' \
                	AND reposcores.EVENT = 'GollumEvent' \
                GROUP BY \
                	users.USERNAME \
                ORDER BY 2 DESC \
                LIMIT 10"

        cursor = self.db.execute(sql)

        html = html + "<table class='table'>"

        for row in cursor:
            html = html + "<tr><td><a href='http://www.github.com/" + str(row[0]) + "'><img src='" + str(row[2]) + "' height='25px'> @" + str(row[0]) +  "</a></td><td>" + str(row[1]) + "</td></tr>"

        html = html + "</table></div>"

        html = html + "</div></div>"

        foot = open("html/footer.html", "r")
        html = html + foot.read()

        return html

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i',
        help='GitHub Client ID (specified as a string)',
        required=False,
    )
    parser.add_argument(
        '-s',
        help='GitHub Client Secret (specified as a string)',
        required=False,
    )

    parser.add_argument(
        '-r',
        help="A repo to base the repo on (specified as 'foo/bar')",
        required=False,
    )


    args = parser.parse_args()

    #a = Rep(sys.argv)
    #a = Rep(args)
    cherrypy.quickstart(Rep(args))
