#! /bin/sh
echo "***************************************************"
echo "This will setup a celery worker setup"
echo "---------------------------------------------------"
if [ -d ".env" ];
then
    echo "Activating celery worker"
else
    echo "No .env present. Try again after running local_setup."
    exit N
fi

#activate virtual env
. .env/bin/activate

export ENV=development

celery -A main.celery worker -l info

deactivate