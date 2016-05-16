Table of Contents
_________________

1. Introduction
2. Requirements
3. Installation
5. Configuration


INTRODUCTION
------------

This program is used to keep an inventory of guitars based on the shops they are
specific to.  When a user is not logged in, they can only view the inventory in each
store.  When they are logged in, they can add new stores, add guitars, edit stores, edit
guitars, and also delete.  Authorization and Authentication are made possible through 
Google Plus and OAuth2.

This guitar inventory web application uses Python, Flask framework, SQLalchemy.  This 
app was tested using only Google Chrome.


REQUIREMENTS 
------------

To run this program, you will need to install the following:

1. SQLalchemy
2. Python 2.7
3. Flask
4. Google Chrome web browser
5. Virtual Box and Vagrant


INSTALLATION
------------

1. Clone the repository from github.com/tomrhoads/GuitarCatalogProject
2. open Git Bash and cd to desired directory
3. type vagrant up
4. type vagrant ssh
5. cd to /vagrant/guitarshop
6. type python database_setup.py
7. type python lotsofguitars.py
8. type python project.py
9. go to Chrome web browser and type https://localhost:5000/

This will start the web application for you being served from a virtual machine.


CONFIGURATION 
-------------

There is nothing modifiable about this program.
