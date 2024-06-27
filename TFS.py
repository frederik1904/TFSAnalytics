import datetime
import json

from requests import Session
from requests.auth import HTTPBasicAuth

from Config import Config
from KeePass import KeePass
import base64

VOTE_STATUS_MAP = {
    '10': 'APPROVED',
    '5': 'APPROVED_WITH_SUGGESTIONS',
    '0': 'NO_VOTE',
    '-5': 'WAITING_FOR_AUTHOR',
    '-10': 'REJECTED'
}


class PullRequestReview:
    data: any = None

    def __init__(self, json: any):
        self.data = json

    def get_vote_status(self) -> str:
        global VOTE_STATUS_MAP
        return VOTE_STATUS_MAP[self.data['vote']]

    def get_author(self) -> str:
        return self.data['uniqueName']


class Comment:
    id: str = None
    author: str = None
    content: str = None
    published_at: datetime.datetime = None
    last_updated: datetime.datetime = None

    def __init__(self, json: any):
        self.id = json['id']
        self.author = json['author']['uniqueName']
        self.content = json['content']
        self.published_at = json['publishedDate']
        self.last_updated = json['lastContentUpdatedDate']


class PullRequestCommentThread:
    data: any
    thread_id: str
    comments: any = []
    COMMENTS: str = 'comments'
    ID: str = 'id'

    def __init__(self, json: any):
        self.data = json
        self.thread_id = json[self.ID]
        self.comments = []
        for comment in json[self.COMMENTS]:
            self.comments.append(Comment(comment))

    def get_thread_id(self) -> str:
        return self.thread_id

    def get_comments(self) -> [Comment]:
        return self.comments

    def get_thread_status(self) -> str:
        return self.data['status']

    def is_comment_thread(self) -> bool:
        return 'Microsoft.TeamFoundation.Discussion.UniqueID' in self.data['properties']

    def is_review_vote(self) -> bool:
        return 'CodeReviewVoteResult' in self.data['properties']

    def get_published_at(self) -> datetime.datetime:
        return self.data['publishedDate']

    def get_review_vote(self):
        global VOTE_STATUS_MAP
        return VOTE_STATUS_MAP[self.data['properties']['CodeReviewVoteResult']['$value']]


class PullRequestComments:
    data: any
    commit_id: str
    comments: any = []
    VALUE = 'value'

    def __init__(self, json: any, commit_id: str):
        self.data = json
        self.commit_id = commit_id
        self.comments = []
        for thread in json[self.VALUE]:
            self.comments.append(PullRequestCommentThread(thread))

    def get_thread_id(self) -> str:
        return self.commit_id

    def get_comment_threads(self) -> [PullRequestCommentThread]:
        return [thread for thread in self.comments if thread.is_comment_thread()]

    def get_review_threads(self):
        return [thread for thread in self.comments if thread.is_review_vote()]


class PullRequest:
    PR: any
    TARGET_BRANCH: str = 'targetRefName'
    STATUS_COMPLETED: str = 'completed'
    STATUS: str = 'status'
    commit_id: str
    TITLE: str = 'title'
    DESCRIPTION: str = 'description'

    reviewers: [PullRequestReview] = []
    comments: PullRequestComments = None

    def __init__(self, json: any, commit_id: str):
        self.PR = json
        self.commit_id = commit_id

        for reviwer in self.PR['reviewers']:
            self.reviewers.append(PullRequestReview(reviwer))

    def is_to_branch(self, branch: str = 'heads/development'):
        return str(self.PR[self.TARGET_BRANCH]).__contains__(branch)

    def is_completed(self):
        return self.PR[self.STATUS] == self.STATUS_COMPLETED

    def get_commit_id(self):
        return self.commit_id

    def get_title(self):
        return self.PR[self.TITLE]

    def get_description(self):
        return self.PR[self.DESCRIPTION]

    def get_target_name(self):
        return str(self.PR[self.TARGET_BRANCH])

    def add_pullrequest_comment(self, comment: PullRequestComments):
        self.comments = comment

    def get_reviewers(self) -> [PullRequestReview]:
        return self.reviewers

    def get_pullrequest_comment(self) -> PullRequestComments:
        return self.comments

    def get_time_to_first_comment(self):
        earliest_comment: datetime.datetime = None

        for thread in self.comments.get_comment_threads():
            if earliest_comment is None or earliest_comment > thread.get_published_at():
                earliest_comment = thread.get_published_at()

        return earliest_comment

    def get_first_reviewer(self) -> (datetime.datetime, str):
        earliest_review: datetime.datetime = None
        earliest_vote: str = None

        for reviewer in self.comments.get_review_threads():
            if earliest_review is None or earliest_review > reviewer.get_published_at():
                earliest_review = reviewer.get_published_at()
                earliest_vote = reviewer.get_review_vote()

        return earliest_review, earliest_vote


class TFS:
    _config: Config = None
    _keepass: KeePass = None
    _session: Session = None

    def __init__(self, config: Config, keepass: KeePass):
        self._config = config
        self._keepass = keepass
        self._session = Session()
        self.auth_check()

    def auth_check(self):
        test = self._session.get(self.get_base_path(), headers=self.prepare_headers())

        if test.status_code != 200:
            raise Exception("Failed to authenticate with TFS")

    def prepare_headers(self):
        username = self._keepass.get_tfs_username()  # This can be an arbitrary value or you can just let it empty
        password = self._keepass.get_tfs_token()
        userpass = username + ":" + password
        b64 = base64.b64encode(userpass.encode()).decode()
        return {"Authorization": "Basic %s" % b64}

    def get_base_path(self):
        return f"{self._config.get_tfs_baseUrl()}/{self._config.get_tfs_organization()}/{self._config.get_tfs_project()}/_apis"

    # https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-request?view=azure-devops-rest-7.0
    def get_pullrequest(self, commit_id: str) -> PullRequest:
        url = f'{self.get_base_path()}/git/repositories/{self._config.get_tfs_repo()}/pullrequests/{commit_id}?api-version=7.0'
        r = self._session.get(url=url, headers=self.prepare_headers())
        if r.status_code == 200:
            return PullRequest(r.json(), commit_id)

        raise Exception(f'Failed to get pull request with {r.json()}')

    def get_pullrequest_comments(self, commit_id: str):
        url = f'{self.get_base_path()}/git/repositories/{self._config.get_tfs_repo()}/pullrequests/{commit_id}/threads?api-version=7.0'
        r = self._session.get(url=url, headers=self.prepare_headers())
        if r.status_code == 200:
            return PullRequestComments(r.json(), commit_id)

        raise Exception(f'Failed to get pull request with {r.json()}')

    # https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-request?view=azure-devops-rest-7.0
    def get_pullrequests_ids(self, target_branch: str) -> [str]:
        url = f'{self.get_base_path()}/git/repositories/{self._config.get_tfs_repo()}/pullrequests/?searchCriteria.targetRefName={target_branch}&api-version=7.0'
        r = self._session.get(url=url, headers=self.prepare_headers())
        if r.status_code == 200:
            result = []
            for pullrequest in r.json()['value']:
                result.append(pullrequest['pullRequestId'])

            return result

        raise Exception(f'Failed to get pull request with {r.json()}')