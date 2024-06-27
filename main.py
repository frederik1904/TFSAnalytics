from Config import Config
from KeePass import KeePass
from TFS import *

conf = Config()
print(conf.get_keepass_path())
print(conf.get_keepass_password())
print(conf.get_tfs_token_path())

keepass = KeePass(conf)
print(keepass.get_tfs_token())

tfs = TFS(conf, keepass)

ids = tfs.get_pullrequests_ids("refs/heads/main")
for id in ids:
    print(id)
    pullrequest = tfs.get_pullrequest(id)
    pullrequest.add_pullrequest_comment(tfs.get_pullrequest_comments(id))

    print(pullrequest.get_time_to_first_comment(), pullrequest.get_first_reviewer())
    print()
    print()