#!/usr/bin/env python
""" Backup MySQL DBs """
import ConfigParser
import logging
import mailer
import subprocess
import sys
import time

# Configuration constants
TIMESTAMP = time.strftime('%Y-%m-%d')

LCL_PTH = '/some/path/here'
CONFIG_FILE = LCL_PTH + '/bin/mysql-dbs.cfg'

LOG_FILE = LCL_PTH + '/log/mysql-backup.log'
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
# End configuration here

def backup_sites(config_file=CONFIG_FILE):
    """ Iterate through site in dbs.cfg """
    logging.debug('Loading config "%s"', config_file)

    conf = ConfigParser.ConfigParser()
    conf.read(config_file)
    sites = conf.sections()

    for site in sites:
        backup_site_dbs(site, conf)

def backup_site_dbs(site, conf):
    """ Perform one mysqldump for each site """
    host = conf.get(site, 'host')
    user = conf.get(site, 'user')
    passwd = conf.get(site, 'passwd')
    path = conf.get(site, 'path')

    backupfile = '%s/%s_%s.sql.gz' % (path, site, TIMESTAMP)

    logging.info('Back up %s DBs to %s', site, backupfile)

    # -R = dump routines, -E = dump events tables
    # neither is required but removes warnings
    # Skip table as we don't want events, but
    # supresses a warning about not backing it up
    cmd = "mysqldump --all-databases -u %s -h %s -p%s " \
        "-R -E | gzip -9 > %s" % (
            user, host, passwd, backupfile
            )

    logging.debug('Cmd = \'%s\'', cmd)

    args = [ 'mysqldump', '--all-databases', '-u', user, '-h', host, "-p%s" % passwd, '-R', '-E' ]

    dump = "/usr/bin/mysqldump --all-databases -u %s -h %s -p\"%s\" -R -E" % (
        user, host, passwd
        )

    gzip = "/bin/gzip -9"

    try:
        pdump = subprocess.Popen(
            args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        backfile = open(backupfile, "w")

        pgzip = subprocess.Popen(
            gzip.split(), stdin=pdump.stdout, stdout=backfile)
        pdump.stdout.close()
        pgzip.communicate()

        pdump.wait()
        backfile.close()

        if pdump.returncode != 0:
            err = pdump.stderr.read()
            logging.debug(err)
            message = "ERROR** %s:CMD=%s | gzip -9" % (err, dump)
            send_email(message, site, conf)

    except OSError, err:
        message = "EXCEPTION** %d:%s:CMD=%s | gzip -9" % (err.errno, err.strerror, dump)
        send_email(message, site, conf)


def send_email(errorcode, site, conf):
    """ Send email ONLY on error """
    mailhost = conf.get(site, 'mailhost')
    msg = mailer.Message()

    msg.From = 'Backup <emailaddress>'
    msg.To = ['MySQL Backup Failures <emailaddress>']
    msg.Subject = 'MySQL Backup Failures %s - %s' % (TIMESTAMP, site)
    msg.Body = 'Failure on %s - %s due to %s' % (
        site, conf.get(site, 'host'), errorcode
        )

    sender = mailer.Mailer(mailhost) # MAILHOST configured at top

    sender.send(msg)

if __name__ == "__main__":
    logging.basicConfig(
        filename=LOG_FILE, format=LOG_FORMAT, level=logging.DEBUG
        )


    if len(sys.argv) > 1:
        cnffile = sys.argv[1]
    else:
        cnffile = CONFIG_FILE

    logging.info('Backup start')

    backup_sites(config_file=cnffile)

    logging.info('Backup ends')
 