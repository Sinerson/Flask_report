import datetime
import json
from json import *
import werkzeug.exceptions
from flask import Flask, render_template, request, url_for, redirect, flash, message_flashed
from werkzeug.exceptions import abort
import pyodbc
import pandas as pd
import openpyxl
from config import DRIVER, SERVER, PORT, USER, PASSW, LANGUAGE, CLIENT_HOST_NAME, CLIENT_HOST_PROC, APPLICATION_NAME, SECRET_KEY


conn_str = ';'.join([DRIVER, SERVER, PORT, USER, PASSW, LANGUAGE, CLIENT_HOST_NAME, CLIENT_HOST_PROC, APPLICATION_NAME])
conn = pyodbc.connect(conn_str, autocommit=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

def get_connection():
	connect = pyodbc.connect(conn_str, autocommit=True)
	cursor = connect.cursor()
	return cursor

def get_reports_group():
	cursor = get_connection()
	cursor.execute("select * from SV..TBP_WEB_REPORTS_LIST where IS_GROUP = 1")
	columns_name = [column[0] for column in cursor.description]
	group_list = []
	for row in cursor.fetchall():
		group_list.append(dict(zip(columns_name, row)))
	cursor.close()
	return group_list

def get_reports_list(id=None):
	if id is None:
		cursor = get_connection()
		cursor.execute("select * from SV..TBP_WEB_REPORTS_LIST where IS_GROUP = 0")
		columns_name = [column[0] for column in cursor.description]
		reports_list = []
		for row in cursor.fetchall():
			reports_list.append(dict(zip(columns_name, row)))
		cursor.close()
		return reports_list
	else:
		cursor = get_connection()
		cursor.execute(f"select * from SV..TBP_WEB_REPORTS_LIST where IS_GROUP = 0 and PARENT_ID = {int(id)}")
		columns_name = [column[0] for column in cursor.description]
		reports_list = []
		for row in cursor.fetchall():
			reports_list.append(dict(zip(columns_name,row)))
		cursor.close()
		return reports_list


@app.route('/', methods=['GET','POST'])
def index():
	reports_group = get_reports_group()
	reports_list = get_reports_list()
	return render_template('index.html', reports_list=reports_list, reports_group = reports_group)


@app.route('/tgusers', methods = ('GET','POST'))
def getTelegramUsers():
	cursor = get_connection()
	if request.method == 'GET':

		cursor.execute("select * from SV..TBP_TELEGRAM_BOT")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()

		return render_template('report.html', data = query_data, reports_list = get_reports_list())#[{**e, "idx" : i+1} for i, e in enumerate(query_data)])
	elif request.method == 'POST':
		nDate = request.form['nDate']
		kDate = request.form['kDate']
		cursor.execute(f"select * from SV..TBP_TELEGRAM_BOT where date between '{nDate}' and '{kDate}'")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()
		return render_template('report.html', data=query_data, reports_list=get_reports_list())
	else:
		abort(501)

@app.route('/devbyaddr', methods = ['GET'])
def getDevicesByAddressList():
	if request.method == 'GET':
		cursor = get_connection()
		cursor.execute("exec MEDIATE..spReportsGroupDevicesByAddress_23032023")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()

		return render_template('report.html', data = query_data, reports_list = get_reports_list())#[{**e, "idx" : i+1} for i, e in enumerate(query_data)])
	else:
		abort(501)


@app.route('/24tvcharge', methods = ['POST','GET'])
def get24TvCharges():
	cursor = get_connection()
	if request.method == 'GET':
		cursor.execute("exec MEDIATE..spSvReports24HTVSubscribers")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()

		return render_template('report.html', data = query_data, reports_list = get_reports_list())
	elif request.method == 'POST':
		nDate = request.form['nDate']
		kDate = request.form['kDate']

		cursor.execute(f"exec MEDIATE..spSvReports24HTVSubscribers")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()

		return render_template('report.html', data=query_data, reports_list=get_reports_list(), nDate = nDate, kDate=kDate)
	else:
		abort(501)


@app.route('/doubleconn', methods = ['POST','GET'])
def getDoubleConnection():
	if request.method == 'GET':
		abort(405)

	elif request.method == 'POST':
		abonType = request.form['abType']
		nDate = request.form['nDate']
		kDate = request.form['kDate']
		cursor = get_connection()
		cursor.execute(f"SV..spSvReportsDoubleConnections_04052023 {int(abonType)},'{nDate}','{kDate}'")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()

		return render_template('report.html', data=query_data, reports_list=get_reports_list(), nDate = nDate, kDate=kDate)
	else:
		abort(501)

#app.route('/getxls', meth)

if __name__ == '__main__':
	run()