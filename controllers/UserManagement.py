import sys
import random, json
from pony import orm
from flask import *
from flask_cors import *
from flask_paginate import Pagination, get_page_parameter
import App
from models.DatabaseContext import *
import hashlib
from datetime import datetime
from controllers.Security import CheckAccess, GetFormAccessControl
from ConfigLogging import *
from io import BytesIO, StringIO
import pandas as pd
import numpy as np
import csv
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
from PollyReports import *
from reportlab.pdfgen.canvas import Canvas
from collections import namedtuple

@App.app.route('/UserManagement/Roles')
def role_page():
    if session.get("user_id") is not None and session.get("fullname") is not None:
        if CheckAccess("Roles", "Read"):
                with db_session:
                        search = False
                        page = request.args.get(get_page_parameter(), type=int, default=1)
                        roles = Roles.select()
                        pagination = Pagination(page=page, total=roles.count(), search=search, record_name='roles', css_framework='bootstrap4')
                        return render_template('UserManagement/roles.html', entries = roles.page(page, 10), pagination=pagination, formAccess = GetFormAccessControl("Roles"))
        else:
                return redirect("/AccessDenied", code=302)
    else:
        return redirect("/", code=302)

@App.app.route('/UserManagement/CreateRole', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def CreateRole():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Roles", "Create"):
                                with db_session:
                                        with db.set_perms_for(Roles):
                                                perm('edit create delete view', group='anybody')
                                                data = request.get_json()
                                                role = Roles(RoleTitle = data['RoleTitle'], Description = data['Description'], LatestUpdateDate = datetime.now())
                                                commit()
                                                message = "Success"
                                                j = json.loads(role.to_json())
                                                InsertInfoLog('create', 'role', 'Roles', j, str(role.RoleID))
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('role', 'create')
                message = str(e)
                return jsonify({'message': message})

@App.app.route('/UserManagement/GetRole', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def GetRole():
    if session.get("user_id") is not None and session.get("fullname") is not None:
        if CheckAccess("Roles", "Read"):
                with db_session:
                        data = request.get_json()
                        query= Roles.select(lambda u: u.RoleID == int(data['RoleID']))
                        mylist = list(query)
                        return jsonify({'RoleID': mylist[0].RoleID, 'RoleTitle': mylist[0].RoleTitle, 'Description': mylist[0].Description})
        else:
                return redirect("/AccessDenied", code=302)
    else:
        return redirect("/", code=302)


@App.app.route('/UserManagement/DeleteRole', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def DeleteRole():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Roles", "Delete"):
                                with db_session:
                                        with db.set_perms_for(Roles):
                                                perm('edit create delete view', group='anybody')
                                                data = request.get_json()
                                                role = Roles.select(lambda r: r.RoleID == int(data["RoleID"]))
                                                j = json.loads(role.to_json())
                                                delete(p for p in Roles if p.RoleID == int(data["RoleID"]))
                                                commit()
                                                message = "Success"
                                                InsertInfoLog('delete', 'role', 'Roles', j, str(data["RoleID"]))
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('role', 'delete')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/EditRole', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def EditRole():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Roles", "Update"):
                                with db_session:
                                         with db.set_perms_for(Roles):
                                                perm('edit create delete view', group='anybody')
                                                data = request.get_json()
                                                role = Roles[int(data['RoleID'])]
                                                role.set(RoleTitle = data['RoleTitle'], Description = data['Description'], LatestUpdateDate = datetime.now())
                                                commit()
                                                j = json.loads(role.to_json())
                                                InsertInfoLog('update', 'role', 'Roles', j,str(data["RoleID"]))
                                                message = "Success"
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('role', 'update')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/RoleAccesses')
def role_access_page():
        if session.get("user_id") is not None and session.get("fullname") is not None:
                if CheckAccess("Role Accesses", "Read"):
                        with db_session:
                                roles = Roles.select()
                                return render_template('UserManagement/roleaccesses.html', roles = roles, formAccess = GetFormAccessControl("Role Accesses"))
                else:
                        return redirect("/AccessDenied", code=302)
        else:
                return redirect("/", code=302)


@App.app.route('/UserManagement/GetRoleAccesses', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def GetRoleAccesses():
        if session.get("user_id") is not None and session.get("fullname") is not None:
                if CheckAccess("Role Accesses", "Read"):
                                with db_session:
                                        data = request.get_json()
                                        id = int(data["RoleID"])
                                        query= db.select('''SELECT r.roleid, r.roletitle, af.appformid, af.appformtitle, ra.creategrant, ra.ReadGrant, ra.UpdateGrant, ra.DeleteGrant, ra.PrintGrant
                                                FROM public.appforms as af cross join public.roles as r
                                                full outer join public.roleaccesses as ra on af.appformid = ra.appformid and r.roleid = ra.roleid
                                                WHERE r.roleid='''+str(id) +'order by r.roleid, af.appformid' )
                                        mylist = list(query)
                                        return jsonify(mylist)
                else:
                        return redirect("/AccessDenied", code=302)
        else:
                return redirect("/", code=302)


@App.app.route('/UserManagement/SetRoleAccesses', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def SetRoleAccesses():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Role Accesses", "Update"):
                                with db_session:
                                         with db.set_perms_for(RoleAccesses):
                                                perm('edit create delete view', group='anybody')
                                                data = request.get_json()
                                                Accesses = data["Accesses"]
                                                for item in Accesses:
                                                        query = RoleAccesses.select(lambda u: u.RoleID.RoleID == int(item['roleId']) and u.AppFormID.AppFormID == int(item['formId']))
                                                        mylist = list(query)
                                                        if len(mylist) > 0:
                                                                roleAccess = RoleAccesses[mylist[0].RoleAccessID]
                                                                roleAccess.set(CreateGrant = bool(item["create"]), ReadGrant = bool(item["read"]), UpdateGrant = bool(item["update"]), DeleteGrant = bool(item["delete"]), PrintGrant = bool(item["print"]), LatestUpdateDate = datetime.now() )
                                                        else:
                                                                RoleAccesses(RoleID = int(item["roleId"]), AppFormID = int(item["formId"]), CreateGrant = bool(item["create"]), ReadGrant = bool(item["read"]), UpdateGrant = bool(item["update"]), DeleteGrant = bool(item["delete"]), PrintGrant = bool(item["print"]), LatestUpdateDate = datetime.now() )
                                                commit()
                                                j = json.loads(Accesses.to_json())
                                                InsertInfoLog('update', 'role accesses', 'RoleAccesses', j,str(data["RoleAccessID"]))
                                                message = "Success"
                                                return jsonify({'message': message})
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('role accesses', 'update')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/Users')
def user_page():
        if session.get("user_id") is not None and session.get("fullname") is not None:
                if CheckAccess("Users", "Read"):
                        with db.set_perms_for(Users):
                                perm('edit create delete view', group='anybody')
                                with db_session:
                                        search = False
                                        page = request.args.get(get_page_parameter(), type=int, default=1)
                                        users = Users.select()
                                        roles = Roles.select()
                                        pagination = Pagination(page=page, total=users.count(), search=search, record_name='users', css_framework='bootstrap4')
                                        return render_template('UserManagement/users.html', users = users.page(page, 10), pagination = pagination, roles = roles, formAccess = GetFormAccessControl("Users"))
                else:
                        return redirect("/AccessDenied", code=302)
        else:
                return redirect("/", code=302)


@App.app.route('/UserManagement/CreateUser', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def CreateUser():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Users", "Create"):
                                with db.set_perms_for(Users):
                                        perm('edit create delete view', group='anybody')
                                        with db_session:
                                                data = request.get_json()
                                                print(data['Password'])
                                                password = hashlib.sha512(str(data['Password']).encode('utf-8')).hexdigest()
                                                user = Users(FirstName = str(data['FirstName']), LastName =str(data['LastName']), Username=str(data['Username']), Password=password, RoleID=int(data['RoleID']), PersonelCode=str(data['PersonelCode']), ManagerID=str(data['ManagerID']), IsActive=True, LatestUpdateDate = datetime.now() )
                                                message = "Success"
                                                commit()
                                                j = json.loads(user.to_json())
                                                InsertInfoLog('create', 'user', 'Users', j,str(data["UserID"]))
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('user', 'create')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/GetUser', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def GetUser():
        if session.get("user_id") is not None and session.get("fullname") is not None:
                if CheckAccess("Users", "Read"):
                        with db_session:
                                data = request.get_json()
                                query= Users.select(lambda u: u.UserID == int(data['UserID']))
                                mylist = list(query)
                                managerID = mylist[0].ManagerID.UserID if mylist[0].ManagerID is not None else ''
                                managerName = mylist[0].ManagerID.FirstName+' '+mylist[0].ManagerID.LastName if mylist[0].ManagerID is not None else ''
                                return jsonify({'UserID': mylist[0].UserID, 'FirstName': mylist[0].FirstName, 'LastName': mylist[0].LastName, 'Username': mylist[0].Username, 'RoleID': mylist[0].RoleID.RoleID, 'RoleTitle': mylist[0].RoleID.RoleTitle, 'PersonelCode': mylist[0].PersonelCode, 'IsActive': mylist[0].IsActive, 'ManagerID': managerID , 'ManagerName': managerName})
                else:
                        return redirect("/AccessDenied", code=302)
        else:
                return redirect("/", code=302)



@App.app.route('/UserManagement/DeleteUser', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def DeleteUser():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Users", "Delete"):
                                with db.set_perms_for(Users):
                                        perm('edit create delete view', group='anybody')
                                        with db_session:
                                                data = request.get_json()
                                                user =Users.select(lambda u: u.UserID == int(data["UserID"]))
                                                j = json.loads(user.to_json())
                                                delete(p for p in Users if p.UserID == int(data["UserID"]))
                                                commit()
                                                InsertInfoLog('delete', 'user', 'Users', j,str(data["UserID"]))
                                                message = "Success"
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('user', 'delete')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/EditUser', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def EditUser():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Users", "Update"):
                                with db.set_perms_for(Users):
                                        perm('edit create delete view', group='anybody')
                                        with db_session:
                                                data = request.get_json()
                                                user = Users[int(data['UserID'])]
                                                user.set(FirstName = str(data['FirstName']), LastName =str(data['LastName']), Username=str(data['Username']), RoleID=int(data['RoleID']), PersonelCode=str(data['PersonelCode']), ManagerID=str(data['ManagerID']), IsActive=True, LatestUpdateDate = datetime.now())
                                                message = "Success"
                                                commit()
                                                j = json.loads(user.to_json())
                                                InsertInfoLog('update', 'user', 'Users', j,str(data["UserID"]))
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('user', 'update')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/UserActivation', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def UserActivation():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Users", "Update"):
                                with db.set_perms_for(Users):
                                        perm('edit create delete view', group='anybody')
                                        with db_session:
                                                data = request.get_json()
                                                user = Users[int(data['UserID'])]
                                                if user.IsActive:
                                                        user.set(IsActive=False, LatestUpdateDate = datetime.now())
                                                else:
                                                        user.set(IsActive=True, LatestUpdateDate = datetime.now())
                                                message = "Success"
                                                commit()
                                                j = json.loads(user.to_json())
                                                InsertInfoLog('update', 'user', 'Users', j,str(data["UserID"]))
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('user', 'user activation')
                message = str(e)
                return jsonify({'message': message})

@App.app.route('/UserManagement/ChangePasswordByUser', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def ChangePasswordByUser():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        with db.set_perms_for(Users):
                                perm('edit create delete view', group='anybody')
                                with db_session:
                                        data = request.get_json()
                                        user = Users[int(data['UserID'])]
                                        oldPassword = hashlib.sha512(str(data['OldPassword']).encode('utf-8')).hexdigest()
                                        message = ""
                                        if user.Password == oldPassword:
                                                newPassword = hashlib.sha512(str(data['NewPassword']).encode('utf-8')).hexdigest()
                                                user.set(Password = newPassword, LatestUpdateDate = datetime.now())
                                                message = "Success"
                                        else:
                                                message = "The old password is not correct"
                                        commit()
                                        j = json.loads(user.to_json())
                                        InsertInfoLog('update', 'user', 'Users', j,str(data["UserID"]))
                                        return jsonify({'message': message})
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('user', 'change password user')
                message = str(e)
                return jsonify({'message': message})


@App.app.route('/UserManagement/ChangePasswordByAdmin', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def ChangePasswordByAdmin():
        try:
                if session.get("user_id") is not None and session.get("fullname") is not None:
                        if CheckAccess("Users", "Update"):
                                with db.set_perms_for(Users):
                                        perm('edit create delete view', group='anybody')
                                        with db_session:
                                                data = request.get_json()
                                                user = Users[int(data['UserID'])]
                                                newPassword = hashlib.sha512(str(data['Password']).encode('utf-8')).hexdigest()
                                                user.set(Password = newPassword, LatestUpdateDate = datetime.now())
                                                message = "Success"
                                                commit()
                                                j = json.loads(user.to_json())
                                                InsertInfoLog('update', 'user', 'Users', j,str(data["UserID"]))
                                                return jsonify({'message': message})
                        else:
                                return redirect("/AccessDenied", code=302)
                else:
                        return redirect("/", code=302)
        except Exception as e:
                InsertErrorLog('user', 'change password admin')
                message = str(e)
                return jsonify({'message': message})

@App.app.route('/UserManagement/ExportReport', methods=['GET', 'POST'])
def UserExportReport():
        if session.get("user_id") is not None and session.get("fullname") is not None:
                if CheckAccess("Users", "Print"):
                        with db_session:
                                if request.form["reportType"] == 'Excel':
                                        output = BytesIO()
                                        writer = pd.ExcelWriter(output, engine='xlsxwriter')
                                        workbook = writer.book
                                        worksheet = workbook.add_worksheet()
                                        bold = workbook.add_format({'bold': True})
                                        worksheet.write('A1', 'No.', bold)
                                        worksheet.write('B1', 'First Name', bold)
                                        worksheet.write('C1', 'Last Name', bold)
                                        worksheet.write('D1', 'Username', bold)
                                        worksheet.write('E1', 'Role Title', bold)
                                        worksheet.write('F1', 'Personel Code', bold)
                                        worksheet.write('G1', 'Manager', bold)
                                        worksheet.write('H1', 'Is Active?', bold)
                                        row = 1
                                        col = 0
                                        users = Users.select()
                                        for item in users:
                                                worksheet.write(row, col, row)
                                                worksheet.write(row, col + 1, item.FirstName)
                                                worksheet.write(row, col + 2, item.LastName)
                                                worksheet.write(row, col + 3, item.Username)
                                                worksheet.write(row, col + 4, item.RoleID.RoleTitle)
                                                worksheet.write(row, col + 5, item.PersonelCode)
                                                if item.ManagerID is not None:
                                                        worksheet.write(row, col + 6, item.ManagerID.FirstName+' '+item.ManagerID.LastName)
                                                else:
                                                        worksheet.write(row, col + 6, None)
                                                worksheet.write(row, col + 7, item.IsActive)
                                                row += 1
                                        writer.close()
                                        output.seek(0)
                                        return send_file(output, attachment_filename="Users-"+datetime.now().strftime("%Y%m%d%H%M%S")+".xlsx", as_attachment=True)
                                elif request.form["reportType"] == 'CVS':
                                        def generate():
                                                with db_session:
                                                        output = StringIO()
                                                        writer = csv.writer(output)
                                                        writer.writerow(('First Name', 'Last Name', 'Username', 'Role Title', 'Personel Code', 'Manager', 'Is Active'))
                                                        yield output.getvalue()
                                                        output.seek(0)
                                                        output.truncate(0)
                                                        users = Users.select()
                                                        for item in users:
                                                                manager = None
                                                                if item.ManagerID is not None:
                                                                        manager = item.ManagerID.FirstName+' '+item.ManagerID.LastName
                                                                writer.writerow((item.FirstName,item.LastName,item.Username,item.RoleID.RoleTitle,item.PersonelCode,manager,item.IsActive))
                                                                yield output.getvalue()
                                                                output.seek(0)
                                                                output.truncate(0)
                                        headers = Headers()
                                        headers.set('Content-Disposition', 'attachment', filename="Users-"+datetime.now().strftime("%Y%m%d%H%M%S")+".cvs")

                                        return Response(
                                                        stream_with_context(generate()),
                                                        mimetype='text/csv', headers=headers
                                        )
                                elif request.form["reportType"] == 'PDF':
                                        with db_session:
                                                with db.set_perms_for(Users):
                                                        currentDateTime = datetime.now()
                                                        perm('edit create delete view', group='anybody')
                                                        users = namedtuple("Users", "UserID FirstName LastName Username RoleID PersonelCode ManagerID IsActive")
                                                        users = select(u for u in Users)[:]
                                                        result = {'data': [{"UserID": p.UserID, "FirstName": p.FirstName, "LastName": p.LastName, "Username": p.Username, "RoleTitle": p.RoleID.RoleTitle, "PersonelCode": p.PersonelCode, "Manager": p.ManagerID.FirstName+' '+p.ManagerID.FirstName if p.ManagerID is not None else '', "IsActive": p.IsActive} for p in users]}
                                                        rpt = Report(result["data"])
                                                        rpt.detailband = Band([
                                                                Element((36, 0), ("Helvetica", 11), key = "FirstName"),
                                                                Element((130, 0), ("Helvetica", 11), key = "LastName"),
                                                                Element((230, 0), ("Helvetica", 11), key = "Username"),
                                                                Element((330, 0), ("Helvetica", 11), key = "RoleTitle"),
                                                                Element((430, 0), ("Helvetica", 11), key = "PersonelCode"),
                                                                Element((530, 0), ("Helvetica", 11), key = "Manager"),
                                                                Element((630, 0), ("Helvetica", 11), key = "IsActive"),
                                                        ])

                                                        rpt.pageheader = Band([
                                                                Element((36, 0), ("Helvetica-Bold", 20), text = "Users List"),
                                                                Element((36, 24), ("Helvetica", 12), text = "First Name"),
                                                                Element((130, 24), ("Helvetica", 12), text = "Last Name"),
                                                                Element((230, 24), ("Helvetica", 12), text = "Username"),
                                                                Element((330, 24), ("Helvetica", 12), text = "Role Title"),
                                                                Element((430, 24), ("Helvetica", 12), text = "Personel Code"),
                                                                Element((530, 24), ("Helvetica", 12), text = "Manager"),
                                                                Element((630, 24), ("Helvetica", 12), text = "Is Active?"),
                                                                Rule((36, 42), 9*72, thickness = 2),
                                                        ])

                                                        rpt.pagefooter = Band([
                                                                Element((72*9.5, 0), ("Helvetica-Bold", 14), text = currentDateTime.strftime("%Y/%m/%d %H:%M:%S"), align = "right"),
                                                                Element((36, 16), ("Helvetica-Bold", 12), sysvar = "pagenumber", format = lambda x: "Page %d" % x),
                                                        ])
                                                        
                                                        filename = "Users-"+currentDateTime.strftime("%Y%m%d%H%M%S")+".pdf"
                                                        output = BytesIO()
                                                        canvas = Canvas(output, (72*11, 72*8.5))
                                                        rpt.generate(canvas)
                                                        canvas.showPage()
                                                        canvas.save()
                                                        pdf_out = output.getvalue()
                                                        output.close()
                                                        response = make_response(pdf_out)
                                                        response.headers['Content-Disposition'] = "attachment; filename="+filename
                                                        response.mimetype = 'application/pdf'
                                                        return response
                else:
                        return redirect("/AccessDenied", code=302)
        else:
                return redirect("/", code=302)