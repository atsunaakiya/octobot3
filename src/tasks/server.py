from pathlib import Path

from flask import Flask, render_template, redirect, request

from src.config import load_config
from src.data import IndexItem
from src.enums import ServiceType, TaskStage, TaskStatus
from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.models.subscribe import SubscribeSource
from src.models.user import UserInfo
from src.services import subscribe_services, pull_services, PullService

template_folder = str(Path(__file__).parent.parent / 'templates')

app = Flask(__name__, template_folder=template_folder)


@app.route("/")
def _index():
    pipelines = load_config().pipeline.items()
    status = ItemInfo.count_status()
    return render_template('index.jinja2', pipelines=pipelines, status=status)


@app.route("/pipeline/<pipeline_name>")
def _pipeline(pipeline_name):
    config = load_config()
    pipeline = config.pipeline[pipeline_name]
    subs = []
    for s in pipeline.subscribe:
        l = [
            (n, subscribe_services[s.service].get_title(n), subscribe_services[s.service].get_url(n))
            for n, channels in SubscribeSource.get_subs_by_channel(*s.service, pipeline_name)]
        subss = subscribe_services[s.service]
        options = subss.options()
        subs.append((s.service[0].value, s.service[1], l, len(l), options))
    status = ItemInfo.count_status()
    return render_template('pipeline.jinja2',
                           pipeline_name=pipeline_name,
                           subs=subs,
                           status=status
                           )


@app.route("/pipeline/<pipeline_name>/subs/add", methods=["POST"])
def _add_subs(pipeline_name):
    service_type = ServiceType(request.form.get("service"))
    service_func = request.form.get("func")
    name = request.form.get("name")
    if name:
        SubscribeSource.add_subs(service_type, service_func, name, pipeline_name)
    return redirect(f"/pipeline/{pipeline_name}")


@app.route("/pipeline/<pipeline_name>/subs/delete", methods=["POST"])
def _delete_subs(pipeline_name):
    service_type = ServiceType(request.form.get("service"))
    service_func = request.form.get("func")
    name = request.form.get("name")
    SubscribeSource.delete_subs(service_type, service_func, name, pipeline_name)
    return redirect(f"/pipeline/{pipeline_name}")


@app.route("/pipeline/<pipeline_name>/items/add", methods=["POST"])
def _add_item(pipeline_name):
    url = request.form.get("url")
    config = load_config()
    pipeline = config.pipeline[pipeline_name]
    for p in pipeline.pull:
        pull = pull_services[p.service]
        item_id = pull.parse_item_id(url)
        if item_id is None:
            continue
        ItemInfo.add_index(IndexItem(service=p.service, item_id=item_id), [pipeline_name])
        ItemInfo.set_status(p.service, item_id, TaskStage.Fetching, TaskStatus.Queued)
        return redirect(f"/pipeline/{pipeline_name}")
    return "Unknown URL"

@app.route("/failures", methods=["GET"])
def _failure_browser_root():
    config = load_config()
    service_types = [
        t
        for t in [ServiceType.Twitter, ServiceType.Pixiv, ServiceType.Fanbox,
                                              ServiceType.Weibo]
        if t in config.api
    ]
    stage_list = [TaskStage.Fetching, TaskStage.Downloading, TaskStage.Posting, TaskStage.Cleaning]
    return render_template('failures_index.jinja2', stage_list=stage_list, service_types=service_types)


@app.route("/failures/reset", methods=["POST"])
def _reset_failure():
    service = ServiceType(request.form.get("service"))
    stage = TaskStage(request.form.get("stage"))
    item_id = request.form.get("item_id")
    ItemInfo.retry_failure(service, item_id)
    return redirect(f'/failures/{service.value}/{stage.value}')


@app.route("/failures/<item_type>/<item_stage>", methods=["GET"])
def _failure_browser(item_type, item_stage):
    item_type = ServiceType(item_type)
    item_stage = TaskStage(item_stage)
    items = ItemInfo.get_failures(service=item_type, stage=item_stage)
    return render_template('failures.jinja2', items=items, stage=item_stage, item_type=item_type)


def launch():
    conf = load_config().server
    connect_db()
    app.run(host=conf.host, port=conf.port)


if __name__ == '__main__':
    launch()
