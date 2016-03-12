# Event Scoring

This document shows the table of base scores that `gh-rep` uses to determine comparitive value between different actions.

Below the table is a list of the different decisions that are made as each event is processed to determine how much of that base score is awarded.

**IMPORTANT NOTE**: These scores and decisions are in no way final.

# Base Scoring

| Event | Base Score |
|-------|-------------|
| CommitCommentEvent | 60 |
| CreateEvent | 30 |
| DeleteEvent | 30 |
| DeploymentEvent | 0 |
| DeploymentStatusEvent | 0 |
| DownloadEvent | 0 |
| FollowEvent | 0 |
| ForkEvent | 20 |
| ForkApplyEvent | 0 |
| GistEvent | 0 |
| GollumEvent | 30 |
| IssueCommentEvent | 50 |
| IssuesEvent | 20 |
| MemberEvent | 0 |
| MembershipEvent | 0 |
| PageBuildEvent | 0 |
| PublicEvent | 100 |
| PullRequestEvent | 100 |
| PullRequestReviewCommentEvent | 80 |
| PushEvent | 80 |
| ReleaseEvent | 100 |
| RepositoryEvent | 0 |
| StatusEvent | 0 |
| TeamAddEvent | 0 |
| WatchEvent | 1 |

# Decisions

## CommitCommentEvent
## CreateEvent
## DeleteEvent
## DeploymentEvent
## DeploymentStatusEvent
## DownloadEvent
## FollowEvent
## ForkEvent
## ForkApplyEvent
## GistEvent
## GollumEvent
## IssueCommentEvent

#### Is this comment a PR comment?

 * Yes: full points
 * No: 50% deduction

## IssuesEvent

#### Points awarded based on issue type

 * Assigned - 90%
 * Unassigned - 90%
 * Labeled - 70%
 * Unlabeled - 70%
 * Opened - 100%
 * Closed - 60%
 * Reopened - 60%

## MemberEvent
## MembershipEvent
## PageBuildEvent
## PublicEvent
## PullRequestEvent
## PullRequestReviewCommentEvent
## PushEvent

#### Has the PR been merged?

 * Yes - full points
 * No - 50%

## ReleaseEvent
## RepositoryEvent
## StatusEvent
## TeamAddEvent
## WatchEvent
