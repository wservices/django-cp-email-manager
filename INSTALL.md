# Install

Run the Django installer in the control panel with the projectname "email-manager".
Replace the directory ~/email-manager.
```bash
mv ~/email-manager/config/settings/.env ~/tmp.env
mv ~/email-manager/RUN ~/RUN.tmp
~/init/email-manager stop
rm -rf ~/email-manager
git clone https://github.com/wservices/django-cp-email-manager ~/email-manager
mv ~/RUN.tmp ~/email-manager/RUN
mv ~/tmp.env ~/email-manager/config/settings/.env
```

Create an API key in the control panel and append the following two lines in the file ~/email-manager/config/settings/.env:
```config
API_URL="https://api.djangoeurope.com/"
API_KEY="INSERT THE API KEY HERE"
```

```bash
cd ~/email-manager/wtools
~/.virtualenvs/email-manager/bin/python3 ../manage.py compilemessages
~/.virtualenvs/email-manager/bin/python3 ../manage.py collectstatic --noinput
~/init/email-manager start
```

Note: Create a Letsencrypt SSL certificate in the control panel and activate the option "HTTPS only".
