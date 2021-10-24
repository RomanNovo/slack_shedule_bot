#!/usr/bin/env bash


mkdir /app/logs 
# Ensure the log file exists
touch /app/logs/crontab.log
cd /app
export $(grep -v '^#' .env | xargs -d '\n')

# Added a cronjob in a new crontab
echo "* * * * * pwd >> /app/logs/crontab.log 2>&1" > /etc/crontab
echo "* * * * * cd /app && /usr/local/bin/python worker.py >> /app/logs/crontab.log 2>&1" > /etc/crontab

# Registering the new crontab
crontab /etc/crontab

# Starting the cron
/usr/sbin/service cron start

# Displaying logs
# Useful when executing docker-compose logs mycron
tail -f /app/logs/crontab.log