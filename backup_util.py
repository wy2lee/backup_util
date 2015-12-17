#!/usr/bin/python

# Program to perfom incremental backups of some directory
#   HACK, HACK, HACK
#
#   Created - 14/04/17 - Wayne Lee (wayne.lee@sickkids.ca)

from optparse import OptionParser, Option, OptionValueError
from calendar import monthrange
import datetime
import glob, os, sys, subprocess

program_name = 'backup_util.py'


#*************************************************************************************
# FUNCTIONS
def run_cmd(sys_cmd, options):
# one line call to output system command and control debug state
    if options.verbose == 1:
        print "> " + sys_cmd
    if options.debug == 0:
        # p = subprocess.Popen(sys_cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # output, errors = p.communicate()
        # return output, errors
        os.system(sys_cmd)
    else:
        return '',''        

def create_new_backup(period, dirs, datestamps, options):
# Copy's old backup into new backup directory using hard links
# Then rsync's with --delete to update new backup directory

    dir_backup_old = '%s/%s.%s' % \
        (dirs['backup_base'], period, datestamps['last'])
        
    dir_backup_new = '%s/%s.%s' % \
        (dirs['backup_base'], period, datestamps['today'])
        
    # check if backup_old exists, if it does create a copy for today's backup [DAY]
    if (period == 'day') and (os.path.exists(dir_backup_old)):
        cmd_cp = 'cp %s %s/%s.%s %s' % \
            (options.cp_options, dirs['backup_base'], period, datestamps['last'], dir_backup_new)
        if options.verbose:
            print "Hard link copy of old backup directory into today's backup"
        run_cmd(cmd_cp, options)
    elif (period != 'day'):     # Any other backup involves copying today's DAY backup into today's PERIOD backup
        if options.verbose:
            print "Hard link today's DAY back into today's %s backup" % (period,)
        cmd_cp = 'cp %s %s/day.%s %s' % \
            (options.cp_options, dirs['backup_base'], datestamps['today'], dir_backup_new)
        run_cmd(cmd_cp, options)
    
    # rsync source to new backup
    dir_source = dirs['input']
    if len(options.login_source) > 0:
        dir_source = '%s:%s' % (options.login_source, dir_source)
    cmd_rsync = 'rsync %s --delete %s/ %s' % \
        (options.rsync_options, dir_source, dir_backup_new)
    if options.verbose:
        print "rsync source into today's backup"
    run_cmd(cmd_rsync, options)    
    
    # cleanup if needed, at most remove 1 backup
    # Don't want to use any loops on the off chance there's a permissions or some other issue
    max_backups = getattr(options,period)
    list_backups = glob.glob( '%s/%s*' % (dirs['backup_base'], period))
    list_backups.sort()
    if len(list_backups) > max_backups:
        cmd_rm = 'rm -rf %s ' % (list_backups[0],)
        if options.verbose:
            print "Remove oldest backup because limit reached"
        run_cmd(cmd_rm, options)
    
    
    
    
def main():
    usage = "Usage: "+program_name+" dir_input dir_backup_base \n"+\
            "   or  "+program_name+" --help";
    parser = OptionParser(usage=usage)
    parser.add_option("--verbose","-v", action="store_true", dest="verbose",
                        default=0, help="Verbose")
    parser.add_option("--debug","-d", action="store_true", dest="debug",
                        default=0, help="debug mode")
    parser.add_option("--login_source", type="string", dest="login_source",
                        default='', help="If target directory is on a different computer (user@server)")
    parser.add_option("--day", type="int", dest="day",
                        default=7, help="[%default] Days of backup (minimum 1)")
    parser.add_option("--week", type="int", dest="week",
                        default=5, help="[%default] Weeks of backup")
    parser.add_option("--month", type="int", dest="month",
                        default=12, help="[%default] Months of backup")
    parser.add_option("--year", type="int", dest="year",
                        default=2, help="[%default] Years of backup")
    parser.add_option("--cycle_week",type="int", dest="cycle_week",
                        default="0", help="Day of the week (0 - Monday, 6 - Sunday) [%default]")
    parser.add_option("--cycle_month",type="int", dest="cycle_month",
                        default="1", help="Day of the month (must be =<28) [%default]")
    parser.add_option("--cycle_year",type="string", dest="cycle_year",
                        default="01-01", help="Day of the year (MM-DD) [%default]")
    parser.add_option("--cp_options",type="string", dest="cp_options",
                        default="-al", help="Options when using cp [%default]")
    parser.add_option("--rsync_options",type="string", dest="rsync_options",
                        default="-rcq", help="Options when using rsync [%default]")
#    parser.add_option("--backup_time",type="string", dest="backup_time",
#                        default="00:05", help="Time to perform backup (24H HH:MM) [%default]")

    # Handle input arguments and options
    options, args = parser.parse_args()
    if len(args) == 0:
        print usage
        sys.exit()
    elif  len(args) != 2:
        parser.error("*** ERROR - Incorrect number of arguments, should be 2, %s provided ") % \
            (len(args),)
    
    dirs ={}
    dirs['input'], dirs['backup_base'] = args
    
    if not os.path.exists(dirs['backup_base']):
        if options.verbose:
            print 'Creating base backup directory'
        cmd_mkdir = 'mkdir %s' % (dirs['backup_base'],)
        run_cmd(cmd_mkdir, options)
    
    # Extract cycle_year into month and day
    try:
        options.cycle_year_month, options.cycle_year_day = map( int,options.cycle_year.split('-'))
    except ValueError:
        raise sys.exit("*** ERROR - Incorrect cycle_year formation, should be MM-DD")

    # QA cycles
    if (options.day < 1) :
        raise sys.exit("*** ERROR - Minimum of 1 daily backup")
    if (options.cycle_month < 1) or (options.cycle_month > 28) :
        raise sys.exit("*** ERROR - cycle_month must be between 1 and 28 [%s]" % (options.cycle_month,))
    if (options.cycle_year_month < 1) or (options.cycle_year_month > 12) :
        raise sys.exit("*** ERROR - cycle_year.month must be between 1 and 12 [%s]" % (options.cycle_year_month,))
    if (options.cycle_year_day < 1) or (options.cycle_year_day > monthrange(2011,options.cycle_year_month)[1]) :
        raise sys.exit("*** ERROR - Invalid cycle_year.day for specified month")
        

    # Check today's date and determine what backups have to be done
    date_today = datetime.date.today()
    datestamps = {}
    datestamps['today'] = '%0.4d%0.2d%0.2d' % \
        (date_today.year, date_today.month, date_today.day )
    
    # In general, run daily backup
    if options.day > 0:
        date_last = date_today - datetime.timedelta(days=1)
        datestamps['last'] = '%0.4d%0.2d%0.2d' % \
            (date_last.year, date_last.month, date_last.day )
        create_new_backup('day', dirs, datestamps, options)
        
    # If it's the right day of the week, maybe run a weekly backup
    if (options.week > 0) and (date_today.weekday() == options.cycle_week):
        date_last = date_today - datetime.timedelta(weeks=1)
        datestamps['last'] = '%0.4d%0.2d%0.2d' % \
            (date_last.year, date_last.month, date_last.day )
        create_new_backup('week', dirs, datestamps, options)
        
    # If it's the right day of the month, maybe run a monthly backup
    if (options.month > 0) and (date_today.day == options.cycle_month):
        if date_today.month == 1:    # Check if it's january
            datestamps['last'] = '%0.4d%0.2d%0.2d' % \
                (date_today.year -1 , 12, options.cycle_month)
        else:
            datestamps['last'] = '%0.4d%0.2d%0.2d' % \
                (date_today.year  , date_today.month -1, options.cycle_month)
        create_new_backup('month', dirs, datestamps, options)
        
    # If it's the right day of the year, maybe run a yearly backup
    if (options.month > 0) and (date_today.day == options.cycle_year_day) and (date_today.month == options.cycle_year_month):
        datestamps['last'] = '%0.4d%0.2d%0.2d' % \
            (date_today.year-1  , options.cycle_year_month, options.cycle_year_day)
        create_new_backup('year', dirs, datestamps, options)
    
            
if __name__ == '__main__' :
    main()




