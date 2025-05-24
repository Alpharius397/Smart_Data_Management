#!/usr/bin/bash

echo -n "Deactivate Conda (1 => Yes, 0 => No): "
read CONDA

conda_deactivate(){
    conda deactivate
}

activate_django_venv(){
    source "$DJANGO"
}

go_to_project(){
    cd "$SMART"
}

start_server(){
    python3 manage.py runserver
}

start_shell(){
    python3 manage.py shell
}

open_file(){
    nano
}

make_file(){
    mkdir "$1"
}

make_app(){
    django-admin startapp "$1"
}

start_mongo(){
    sudo systemctl start mongod
}

status_mongo(){
    sudo systemctl status mongod
}

stop_mongo(){
    sudo systemctl stop mongod
}

restart_mongo(){
    sudo systemctl restart mongod
}

dump_data(){
    mongodump --host="127.0.0.1:27017" --db="$1" --collection="$2" --out="$SMART/dump"
}

restore_from_dump(){
    mongorestore --nsInclude="$1.$2" "$SMART/dump/"
}

if [ "$CONDA" -eq 1 ]; then
    conda_deactivate
fi

activate_django_venv
go_to_project

CHOICE=0

while true; do
    echo -e "\nChoose an option:"
    echo "1. Start Mongo"
    echo "2. Exit Mongo"
    echo "3. Restart Mongo"
    echo "4. Get DB dump"
    echo "5. Restore DB from dump"
    echo "6. Get MongoDB status"
    echo "7. Exit"
    echo -n "Enter your choice: "
    read CHOICE

    case "$CHOICE" in
        1) start_mongo ;;
        2) stop_mongo ;;
        3) restart_mongo ;;
        4)
            echo -n "Enter Database name: "
            read DB
            echo -n "Enter Collection name: "
            read COLL
            dump_data "$DB" "$COLL"
            ;;
        5)
            echo -n "Enter Database name: "
            read DB
            echo -n "Enter Collection name: "
            read COLL
            restore_from_dump "$DB" "$COLL"
            ;;
        6) status_mongo ;;
        7) echo "Exiting..."; break ;;
        *) echo "Incorrect choice. Please try again." ;;
    esac
done

