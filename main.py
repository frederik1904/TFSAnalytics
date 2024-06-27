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
pullrequest = tfs.get_pullrequest("1")
print(pullrequest.PR)
pullrequest.add_pullrequest_comment(tfs.get_pullrequest_comments("1"))

print(pullrequest.get_time_to_first_comment(), pullrequest.get_first_reviewer())
for thread in pullrequest.get_pullrequest_comment().get_comment_threads():
    print(thread.is_comment_thread())
    if thread.is_comment_thread():
        print(thread.get_thread_status())
        for comment in thread.get_comments():
            print("\t", comment.author, comment.content)
