@echo off

@echo activate nytaxi...
call activate nytaxi

@echo start server
call python app.py

@echo deactivate nytaxi
call deactivate