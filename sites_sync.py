#!/usr/bin/env python
""" Web site RSYNC backup """

import subprocess
import time
import mailer
import logging

# config
BASE_PTH = '/path/to/back/up/to'
APP_PTH = '/path/to/logs/etc'
LOG_PTH = APP_PTH + '/log/'
LCL_PTH = BASE_PTH + '/rsync/'

CONNS = [
 { 'host':'domain.tld', 'user':'username',
   'remote_dir':'some/long/path/public_html', 'port':'22' },
 { 'host':'ipaddress', 'user':'username',
   'remote_dir':'public_html', 'port':'2510' },
 
]

def send_email(errorcode):
    """ Send email ONLY in case of error condition """
    # Email Settings
    host = 'hostname/ip'
    fromemail = 'SendName <error@domain.tld>'
    toemail = ['ToName <someone@domain.tld>']
    filestamp = time.strftime('%Y-%m-%d')
    subject = 'Rsync Backup Failures ' + filestamp

    msg = mailer.Message()
    msg.From = fromemail
    msg.To = toemail
    msg.Body = errorcode
    msg.Subject = subject
    
    sender = mailer.Mailer(host)
    sender.send(msg)

def do_backup(conns) :
    """ Loop through connection details performing rsync backup """
    logging.debug('Loop through (%d) connections', len(conns))
    for cdt in conns :
        try:
            lpth = LCL_PTH + cdt['host']
            logging.info('Back up "%s" to "%s"', cdt['host'], lpth)

            rsync = "/usr/bin/rsync -avz --delete -e "
            ssh_str = '\'ssh -o GSSAPIAuthentication=no -p %s\' ' % (cdt['port'])
            source = '%s@%s:%s ' % (cdt['user'], cdt['host'], cdt['remote_dir'])
            dest = LCL_PTH + cdt['host']

            cmd = rsync + ssh_str + source + dest

            logging.debug('Command = "' + cmd + '"')

            proc = subprocess.Popen([cmd], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()

            logging.debug('Output = "%s"', out.strip())
            logging.debug('Err = "%s"', err.strip())

        except OSError, message:
            errorcode = str(message)
            logging.debug('Exception = "%s"', errorcode.strip())
            send_email(errorcode)

    logging.debug('Loop ends')

LOGFORMAT = "%(asctime)s:%(levelname)s:%(message)s"

logging.basicConfig(filename=LOG_PTH+'sites-rsync.log',
                    format=LOGFORMAT, level=logging.INFO)
logging.info('Backup start')

do_backup(CONNS)

logging.info('Backup ends')

