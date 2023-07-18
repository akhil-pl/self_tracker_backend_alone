#! /bin/sh
echo "***************************************************"
echo "This will setup a celery beat setup"
echo "---------------------------------------------------"
if [ -d ".env" ];
then
    echo "Activating celery beat to track time"
else
    echo "No .env present. Try again after running local_setup."
    exit N
fi

#activate virtual env
. .env/bin/activate

export ENV=development

celery -A main.celery beat --max-interval 1 -l info

deactivate