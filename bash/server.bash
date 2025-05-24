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

custom_option(){
    python3 manage.py "$1"
}

migration(){
    python3 manage.py makemigrations "$1"
    python3 manage.py migrate "$1"
}

if [ "$CONDA" -eq 1 ]; then
    conda_deactivate
fi

activate_django_venv
go_to_project

CHOICE=0

while true; do
    echo -e "\nChoose an option:"
    echo "0. Start Shell"
    echo "1. Start Server"
    echo "2. Do Management Command (manage.py)"
    echo "3. Make Migrations"
    echo "4. Exit"
    echo -n "Enter your choice: "
    read CHOICE

    case "$CHOICE" in
        1)
            start_server
            ;;
        0)
            start_shell
            ;;
        2)
            echo -n "Enter an option for manage.py: "
            read OPT
            custom_option "$OPT"
            ;;
        3)
            echo -n "Enter Apps to migrate: "
            read APP
            migration "$APP"
            ;;
        4)
            echo "Exiting..."
            break
            ;;
        *)
            echo "Incorrect Choice! Please try again."
            ;;
    esac
done

