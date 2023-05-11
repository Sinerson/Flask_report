import datetime, os
from datetime import datetime, timedelta
import json
from json import *
import werkzeug.exceptions
from flask import Flask, render_template, request, url_for, redirect, flash, make_response, session, g, send_file
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
import pandas as pd
import numpy as np
import openpyxl
import xlsxwriter
from io import BytesIO
from config import DRIVER, SERVER, PORT, USER, PASSW, LANGUAGE, CLIENT_HOST_NAME, CLIENT_HOST_PROC, APPLICATION_NAME, SECRET_KEY


conn_str = ';'.join([DRIVER, SERVER, PORT, USER, PASSW, LANGUAGE, CLIENT_HOST_NAME, CLIENT_HOST_PROC, APPLICATION_NAME])
conn = pyodbc.connect(conn_str, autocommit=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

def get_connection():
	connect = pyodbc.connect(conn_str, autocommit=True)
	cursor = connect.cursor()
	return cursor

class Reports():
	def getGroup():
		cursor = get_connection()
		cursor.execute("select * from SV..TBP_WEB_REPORTS_LIST where IS_GROUP = 1")
		columns_name = [column[0] for column in cursor.description]
		group_list = []
		for row in cursor.fetchall():
			group_list.append(dict(zip(columns_name, row)))
		cursor.close()
		return group_list

	def getList(id=None):
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
	def makeExcel():
		df_1 = pd.DataFrame(np.random.randint(0,10,size=(10,4)), columns=list('ABCD'))
		output = BytesIO()
		writer = pd.ExcelWriter(output, engine='xlsxwriter')
		df_1.to_excel(writer,startrow=0, merge_cells=False, sheet_name='Sheet_1')
		workbook = writer.book
		worksheet = writer.sheets["Sheet_1"]
		format = workbook.add_format()
		format.set_bg_color('#eeeeee')
		worksheet.set_column(0,9,28)
		writer.close()
		output.seek(0)
		return send_file(output,download_name="testing.xlsx",as_attachment=True)


class User():
	def getUser(username, password):
		if username and password is not None:
			cursor = get_connection()
			cursor.execute(f"select USER_CODE,rtrim(USER_NAME) as USER_NAME,rtrim(USER_PASSWORD) as USER_PASSWORD,"
			               f"rtrim(USER_STATUS) as USER_STATUS,rtrim(FULL_NAME) as FULL_NAME, GROUP_CODE "
			               f"from INTEGRAL..USERS "
			               f"where USER_ACTIVE = '1' and USER_NAME = '{username}' and USER_PASSWORD = '{password}'")
			columns_name = [column[0] for column in cursor.description]
			user = []
			for row in cursor.fetchall():
				user.append(dict(zip(columns_name, row)))
			cursor.close()
			return user
		else:
			return None
	def login(Login, Password=None):
		if request.method == 'POST':
			session.permanent = True
			app.permanent_session_lifetime = timedelta(hours=8)
			if not Password:
				session['logged_in'] = True
				session['Login'] = Login
			else:
				user_info = User.getUser(Login, Password)
				session['logged_in'] = True
				session['Login'] = Login
				for item in user_info:
					session['FullName'] = item['FULL_NAME']
			return True
	def logout(self):
		session.pop('logged_in', False)
		session.clear()
		return redirect('/')


@app.route('/', methods=['GET','POST'])
def form_authorization():
	if session.get('logged_in') == True:
		return redirect('/index')
	elif request.method == 'POST':
		Login = request.form.get('Login')
		Password = request.form.get('Password')
		psw_hash = generate_password_hash(Password)
		user = User.getUser(Login,Password)
		if not user:
			return render_template('auth_bad.html')
		else:
			User.login(Login, Password)
			for item in user:
				if item['USER_NAME'] == Login and check_password_hash(psw_hash, item['USER_PASSWORD']) is True or g.user is not None:
					return redirect('/index')
				else:
					return render_template('auth_bad.html')
	elif request.method == 'GET':
		return render_template('auth.html')


@app.route('/index', methods=['GET','POST'])
def index():
	if session.get('logged_in') == True:
		reports_group = Reports.getGroup()
		reports_list = Reports.getList()
		Reports.makeExcel()
		return render_template('index.html', reports_list=reports_list, reports_group = reports_group, user_info = session.get('FullName'))
	else:
		return redirect('/')


@app.route('/logout', methods=['GET'])
def logout():
	FullName = session.get('FullName')
	User.logout(session.get('Login'))
	return render_template('logout.html', name=FullName)


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

		return render_template('report.html', data = query_data, reports_list = Reports.getList())#[{**e, "idx" : i+1} for i, e in enumerate(query_data)])
	elif request.method == 'POST':
		nDate = request.form['nDate']
		kDate = request.form['kDate']
		cursor.execute(f"select * from SV..TBP_TELEGRAM_BOT where date between '{nDate}' and '{kDate}'")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()
		return render_template('report.html', data=query_data, reports_list=Reports.getList())
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

		return render_template('report.html', data = query_data, reports_list = Reports.getList())#[{**e, "idx" : i+1} for i, e in enumerate(query_data)])
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

		return render_template('report.html', data = query_data, reports_list = Reports.getList())
	elif request.method == 'POST':
		nDate = request.form['nDate']
		kDate = request.form['kDate']

		cursor.execute(f"exec MEDIATE..spSvReports24HTVSubscribers")
		columns = [column[0] for column in cursor.description]
		query_data = []
		for row in cursor.fetchall():
			query_data.append(dict(zip(columns, row)))
		cursor.close()

		return render_template('report.html', data=query_data, reports_list=Reports.getList(), nDate = nDate, kDate=kDate)
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

		return render_template('report.html', data=query_data, reports_list=Reports.getList(), nDate = nDate, kDate=kDate)
	else:
		abort(501)

if __name__ == '__main__':
	run()