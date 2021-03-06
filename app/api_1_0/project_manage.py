from flask import jsonify, request
from . import api
from app.models import *
import json
from ..util.login_require import login_required
from flask_login import current_user


@api.route('/proGather/list')
def get_pro_gather():
    # if current_user.id == 4:
    _pros = Project.query.all()
    my_pros = Project.query.filter_by(user_id=current_user.id).first()
    pro = {}
    pro_url = {}
    scene_config_lists = {}

    #   获取每个项目下的模块名字
    for p in _pros:
        modules = Module.query.filter_by(project_id=p.id).all()
        if modules:
            pro[p.name] = [{'name': _gat.name, 'moduleId': _gat.id} for _gat in modules]
        else:
            pro[p.name] = ['']

        config_list = Config.query.order_by(Config.num.asc()).filter_by(project_id=p.id).all()
        if config_list:
            scene_config_lists[p.name] = [{'name': _config_list.name, 'configId': _config_list.id} for _config_list in
                                          config_list]
        else:
            scene_config_lists[p.name] = ['']

    # 获取每个项目下的用例集
    set_list = {}
    scene_list = {}
    for p in _pros:
        sets = CaseSet.query.filter_by(project_id=p.id).order_by(CaseSet.num.asc()).all()
        set_list[p.name] = [{'label': s.name, 'id': s.id} for s in sets]

        # 获取每个用例集的用例
        for s1 in sets:
            scene_list["{}".format(s1.id)] = [{'label': scene.name, 'id': scene.id} for scene in
                                              Case.query.filter_by(case_set_id=s1.id).all()]

            # scene_list["abc"] = [{'label': 'aaaaa', 'id': 1},{'label': 'qqqqqq', 'id': 2}]

    # 获取每个项目下的url
    for p in _pros:
        # pro_url[p.name] = []
        if p.environment_choice == 'first':
            pro_url[p.name] = json.loads(p.host)
        elif p.environment_choice == 'second':
            pro_url[p.name] = json.loads(p.host_two)
        elif p.environment_choice == 'third':
            pro_url[p.name] = json.loads(p.host_three)
        elif p.environment_choice == 'fourth':
            pro_url[p.name] = json.loads(p.host_four)

    if my_pros:
        my_pros = {'pro_name': my_pros.name, 'model_list': pro[my_pros.name]}
    return jsonify(
        {'data': pro, 'urlData': pro_url, 'status': 1, 'user_pro': my_pros, 'config_name_list': scene_config_lists,
         'set_list': set_list, 'scene_list': scene_list})


@api.route('/project/find', methods=['POST'])
@login_required
def find_project():
    data = request.json
    project_name = data.get('projectName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    if project_name:
        _data = Project.query.filter(Project.name.like('%{}%'.format(project_name))).all()
        if not _data:
            return jsonify({'msg': '没有该项目', 'status': 0})
    else:
        pagination = Project.query.order_by(Project.id.asc()).paginate(page, per_page=per_page, error_out=False)
        _data = pagination.items
        total = pagination.total

    project = [{'name': c.name, 'principal': c.principal, 'id': c.id, 'host': c.host, 'host_two': c.host_two,
                'host_three': c.host_three, 'host_four': c.host_four} for c in _data]

    return jsonify({'data': project, 'total': total, 'status': 1})


@api.route('/project/add', methods=['POST'])
@login_required
def add_project():
    data = request.json
    project_name = data.get('projectName')
    principal = data.get('principal')
    environment_choice = data.get('environmentChoice')
    host = json.dumps(data.get('host'))
    host_two = json.dumps(data.get('hostTwo'))
    host_three = json.dumps(data.get('hostThree'))
    host_four = json.dumps(data.get('hostFour'))
    ids = data.get('id')
    header = data.get('header')
    variable = data.get('variable')
    if ids:
        old_project_data = Project.query.filter_by(id=ids).first()
        if Project.query.filter_by(name=project_name).first() and project_name != old_project_data.name:
            return jsonify({'msg': '项目名字重复', 'status': 0})
        else:
            old_project_data.name = project_name
            old_project_data.principal = principal
            old_project_data.environment_choice = environment_choice
            old_project_data.host = host
            old_project_data.host_two = host_two
            old_project_data.host_three = host_three
            old_project_data.host_four = host_four
            old_project_data.headers = header
            old_project_data.variables = variable
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Project.query.filter_by(name=project_name).first():
            return jsonify({'msg': '项目名字重复', 'status': 0})

        else:
            new_project = Project(name=project_name, principal=principal, host=host, host_two=host_two,
                                  user_id=current_user.id, environment_choice=environment_choice,
                                  host_three=host_three, host_four=host_four, headers=header, variables=variable)
            db.session.add(new_project)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/project/del', methods=['POST'])
@login_required
def del_project():
    data = request.json
    ids = data.get('id')
    _edit = Project.query.filter_by(id=ids).first()
    model = Module.query.filter_by(project_id=_edit.id).first()
    if current_user.id != _edit.user_id:
        return jsonify({'msg': '不能删除别人创建的项目', 'status': 0})
    if model:
        return jsonify({'msg': '请先删除项目下的模块', 'status': 0})
    if Case.query.filter_by(project_id=_edit.id).first():
        return jsonify({'msg': '请先删除项目下的业务集', 'status': 0})
    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/project/edit', methods=['POST'])
@login_required
def edit_project():
    data = request.json
    model_id = data.get('id')
    _edit = Project.query.filter_by(id=model_id).first()
    _data = {'pro_name': _edit.name,
             'principal': _edit.principal,
             'host': json.loads(_edit.host),
             'host_two': json.loads(_edit.host_two),
             'host_three': json.loads(_edit.host_three),
             'host_four': json.loads(_edit.host_four),
             'headers': json.loads(_edit.headers),
             'environment_choice': _edit.environment_choice,
             'variables': json.loads(_edit.variables)}

    return jsonify({'data': _data, 'status': 1})
