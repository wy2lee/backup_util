# backup_util
Generic utility to run periodic backups

Basic usage is to put a call to backup_util.py in your crontab

5 0 * * * /usr/local/bin/python/backup_util.py --login_source=root@mrwiki /var/www/html /data8/mrwiki/var_www_html > /dev/null 2>&1

You may need to setup an sshkey pair to facilitate...
