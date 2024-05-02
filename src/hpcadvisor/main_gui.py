import json
import os
import random
import sys
import time
from datetime import datetime
from subprocess import Popen

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.web.cli as stcli
from matplotlib import cm
from matplotlib.patches import Rectangle

from hpcadvisor import (advice_generator, data_collector, dataset_handler,
                        logger, plot_generator, taskset_handler, utils)

log = logger.logger

# TODO: this entire code needs to be refactored!!
# TODO: this entire code needs to be refactored!!
# TODO: this entire code needs to be refactored!!

execution_tracker_filename = "progress.txt"


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


current_dir = os.path.dirname(os.path.abspath(__file__))
style_css_path = os.path.join(current_dir, "./style.css")
local_css(style_css_path)

st.session_state["executionOn"] = False

debug = False
userinput = None


def wait_execution(execution_placeholder):
    while True:
        last_line = ""
        if os.path.exists(execution_tracker_filename):
            with open(execution_tracker_filename, "r") as file:
                lines = file.readlines()
            if lines:
                last_line = lines[-1].strip()

            if last_line == "all_done":
                return
        time.sleep(2)

        last_line = "status: " + last_line
        execution_placeholder.write(last_line)


def disable(b):
    st.session_state["disabled"] = b


def create_deployment(user_input_file):
    st.write("### Create Deployments ")

    #   defaults = _get_defaults()

    user_input = utils.get_userinput_from_file(user_input_file)
    text_subscription = st.text_input("Azure subscription", user_input["subscription"])
    text_region = st.text_input("Azure region", user_input["region"])
    text_deployname = st.text_input("Deployment name (optional)")

    if (
        "run_createdeploy_button" in st.session_state
        and st.session_state.run_createdeploy_button == True
    ):
        st.session_state.running = True
    else:
        st.session_state.running = False

    if st.button(
        "Create deployment",
        disabled=st.session_state.running,
        key="run_createdeploy_button",
    ):
        st.write("## Deployment ")
        if (
            not "deployExecutionOn" in st.session_state
            or st.session_state["deployExecutionOn"] == False
        ):
            st.session_state["deployExecutionOn"] = True

            if text_deployname:
                rg_prefix = text_deployname
            else:
                rg_prefix = user_input["rgprefix"] + utils.get_random_code()

            st.text(f"Creating deployment: {rg_prefix}")
            st.text("This will take a while. Please wait...")

            env_file = utils.generate_env_file(rg_prefix, user_input)

            utils.execute_env_deployer(env_file, rg_prefix, debug)

            st.session_state["deployExecutionOn"] = False
            st.session_state.output = "output generated"
            st.rerun()

            if "output" in st.session_state:
                st.success("Deployment environment created")
                st.text("Go to view deployment button for details.")
                time.sleep(5)
            st.session_state["executionOn"] = False


def view_deployments():
    st.write("## Deployments ")

    deployments = utils.list_deployments()

    label = f"Select deployment (total = {len(deployments)}): "

    selected_item = st.selectbox(label, deployments)


def gen_advice_table(datapoints, datafilter_input):
    pareto_front = advice_generator.gen_advice_exectime_vs_cost(
        None, datapoints, datafilter_input
    )

    if pareto_front is None:
        log.error("No advice generated")
        return

    title = "noappinput"

    if datafilter_input:
        appinputs = datafilter_input["appinputs"]
        title = " ".join([f"{key}={value} " for key, value in appinputs.items()])

    return title, pareto_front


def view_advice():
    st.write("### Advice ")

    st.text("")
    uploaded_file = st.file_uploader(
        "Choose data filter file (optional)", accept_multiple_files=False, type=["json"]
    )

    datafilter_file = None
    if uploaded_file:
        bytes_data = uploaded_file.read()
        datafilter_file = json.loads(bytes_data)

    # st.write("loaded data filter file:", uploaded_file.name)

    appname = None
    deployment = None
    # TODO support multiple deployments via GUI

    if datafilter_file:
        if "appname" in datafilter_file:
            appname = datafilter_file["appname"]
        if "deployment" in datafilter_file:
            deployment = datafilter_file["deployment"]

    appname = st.text_input("Application name", appname)
    deployment = st.text_input("Deployment (optional)", deployment)

    datafilter = {}
    if appname:
        datafilter["appname"] = appname
    if deployment:
        datafilter["deployment"] = deployment

    dataset_file = utils.get_dataset_filename()

    appinputs = []
    if not os.path.exists(dataset_file):
        log.error("Dataset file not found: " + dataset_file)
        return

    datapoints = dataset_handler.get_datapoints(dataset_file, datafilter)

    if not datapoints:
        log.error("No datapoints found. Check dataset and datafilter files")
        return

    appinputs = dataset_handler.get_appinput_combinations(datapoints)

    datafilter_appinputs = []
    for appinput in appinputs:
        filter = {}
        filter["appinputs"] = appinput
        datafilter_appinputs.append(filter)

    if st.button(
        "Get advice",
        key="run_createadvice_button",
    ):
        st.write("## Advice ")
        st.write("This will take a while. Please wait...")
        advice_data = {}
        if datafilter_appinputs:
            for datafilter_appinput_entry in datafilter_appinputs:
                title, pareto_front = gen_advice_table(
                    datapoints, datafilter_appinput_entry
                )
                advice_data[title] = pareto_front
        else:
            title, pareto_front = gen_advice_table(
                table_id, datapoints, datafilter_appinputs
            )

        for title, pareto_front in advice_data.items():
            if title != "noappinput":
                st.markdown(f"##### Appinput: {title}")

            df = pd.DataFrame(
                pareto_front, columns=["Exectime", "Cost", "Nodes", "SKU"]
            )
            st.table(df)

    st.text("")
    st.text("")
    st.text("")


def gen_core_plots(st, plot_id, datapoints, dynamic_filters, plotdir):
    plot_file = "plot_" + str(plot_id) + "_exectime_vs_numvms.pdf"

    plot_generator.gen_plot_exectime_vs_numvms(
        st, datapoints, dynamic_filters, plotdir, plot_file
    )
    plot_id += 1
    plot_file = "plot_" + str(plot_id) + "_exectime_vs_cost.pdf"

    plot_generator.gen_plot_exectime_vs_cost(
        st, datapoints, dynamic_filters, plotdir, plot_file
    )


def show_plot_files(st, datapoints, dynamic_filter_items):
    plot_id = 0
    plotdir = None

    if dynamic_filter_items:
        for dynamic_filter in dynamic_filter_items:
            gen_core_plots(st, plot_id, datapoints, dynamic_filter, plotdir)
            plot_id += 2
    else:
        gen_core_plots(st, plot_id, datapoints, dynamic_filter_items, plotdir)


def view_plot():
    st.write("### Plots ")

    st.text("")
    st.text("")
    st.text("")

    st.text("")
    uploaded_file = st.file_uploader(
        "Choose data filter file (optional)",
        key="fileupload_view_plot",
        accept_multiple_files=False,
        type=["json"],
    )

    datafilter_file = None
    if uploaded_file:
        bytes_data = uploaded_file.read()
        datafilter_file = json.loads(bytes_data)

    # st.write("loaded data filter file:", uploaded_file.name)

    appname = None
    deployment = None
    # TODO support multiple deployments via GUI

    if datafilter_file:
        if "appname" in datafilter_file:
            appname = datafilter_file["appname"]
        if "deployment" in datafilter_file:
            deployment = datafilter_file["deployment"]

    appname = st.text_input(
        "Application name", appname, key="textinput_viewplot_appname"
    )
    deployment = st.text_input(
        "Deployment (optional)", deployment, key="textinput=viewplot_deployment"
    )

    datafilter = {}
    if appname:
        datafilter["appname"] = appname
    if deployment:
        datafilter["deployment"] = deployment

    dataset_file = utils.get_dataset_filename()

    appinputs = []
    if not os.path.exists(dataset_file):
        log.error("Dataset file not found: " + dataset_file)
        return

    datapoints = dataset_handler.get_datapoints(dataset_file, datafilter)

    if not datapoints:
        log.error("No datapoints found. Check dataset and datafilter files")
        return

    appinputs = dataset_handler.get_appinput_combinations(datapoints)

    datafilter_appinputs = []
    for appinput in appinputs:
        filter = {}
        filter["appinputs"] = appinput
        datafilter_appinputs.append(filter)

    if st.button(
        "Get plots",
        key="run_createplot_button",
    ):
        st.write("## Plots ")
        st.write("Generating plots. Please wait...")

        show_plot_files(st, datapoints, datafilter_appinputs)

    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")


def _get_str(data):
    if isinstance(data, list):
        return ",".join(str(x) for x in data)
    else:
        return str(data)


def _get_app_inputs(appinputs):
    data_app_input = {}
    for line in appinputs.splitlines():
        if line.strip():
            key, value = line.split("=")
            data_app_input[key] = value.split(",")

    return data_app_input


def get_str_from_userinput_list(userinput, key):
    if key in userinput:
        if type(userinput[key]) is not list:
            return str(userinput[key])
        return ",".join(str(x) for x in userinput[key])
    else:
        return ""


def get_textfield_from_appinput(userinput):
    if "appinputs" not in userinput:
        return ""

    appinputs = userinput["appinputs"]
    appinput_str = ""
    for key, value in appinputs.items():
        appinput_str += f"{key.upper()}={_get_str(value)}\n"

    return appinput_str


def get_json_from_input(text_input):
    # transfor a,b,c into ["a", "b", "c"]
    if "," in text_input:
        return text_input.split(",")
    else:
        return [text_input]


def start_datacollection(user_input_file):
    st.write("### Data Collector ")

    st.text("")
    st.text("")
    st.text("")

    userinput = utils.get_userinput_from_file(user_input_file)

    task_filename = ""

    deployments = utils.list_deployments()

    label = f"Select deployment (total = {len(deployments)}): "

    deployment = st.selectbox(label, deployments)

    str_skus = get_str_from_userinput_list(userinput, "skus")
    print("str_skus=", str_skus)
    str_nnodes = get_str_from_userinput_list(userinput, "nnodes")
    str_ppr = get_str_from_userinput_list(userinput, "ppr")
    text_skus = st.text_input("SKUs", str_skus, key="field_sku")
    text_nnodes = st.text_input("Number of nodes", str_nnodes, key="field_nnodes")
    text_ppr = st.text_input("Processes per resource (%)", str_ppr, key="field_ppr")

    textfield_appinput = get_textfield_from_appinput(userinput)
    text_appinput = st.text_area(
        "Application input per line (<variable=value>)",
        textfield_appinput,
        key="appinput_info",
    )

    field_appsetup = st.text_input(
        "App setup script (git URL)",
        userinput["appsetupurl"],
        key="app_url_setup",
    )

    if "gentasks_key" not in st.session_state:
        st.session_state.gentasks_key = False

    button_show_tasks = st.button("Show/Hide Tasks", key="button_show_tasks")

    if button_show_tasks and st.session_state.gentasks_key == False:
        st.session_state.gentasks_key = True
    elif button_show_tasks and st.session_state.gentasks_key == True:
        st.session_state.gentasks_key = False

    if st.session_state.gentasks_key:
        task_filename = utils.get_task_filename(deployment)
        st.session_state["task_filename"] = task_filename

        data_system = {}
        data_system["sku"] = text_skus.split(",")
        data_system["nnodes"] = text_nnodes.split(",")
        data_system["ppr"] = text_ppr.split(",")

        data_app_input = {}
        for line in text_appinput.splitlines():
            if line.strip():
                key, value = line.split("=")
                data_app_input[key] = value.split(",")
        #
        appname = userinput["appname"]
        tags = []
        data = taskset_handler.generate_tasks(
            task_filename, data_system, data_app_input, appname, tags
        )
        df = pd.DataFrame(data)
        df = df.set_index("id")

        df.index.name = "task"

        st.dataframe(df, height=200, width=700)

    if (
        "run_datacollector_button" in st.session_state
        and st.session_state.run_datacollector_button == True
    ):
        st.session_state.running_collection = True
    else:
        st.session_state.running_collection = False

    if st.button(
        "Start Data Collection",
        disabled=st.session_state.running_collection,
        key="run_datacollector_button",
    ):
        execution_placeholder = st.empty()

        st.text("This will take a while. Please wait...")
        st.session_state["executionCollectionOn"] = True

        task_filename = utils.get_task_filename(deployment)

        env_file = utils.get_deployments_file(deployment)
        dataset_filename = utils.get_dataset_filename()
        data_collector.collect_data(
            task_filename, dataset_filename, env_file, clear_deployment=False
        )

        log.info(f"finish execution for {deployment}")
        st.success("Benchmark data generated!")
        st.session_state.output = "output generated"
        st.rerun()

        st.session_state["executionCollectionOn"] = False
        st.session_state["running_collection"] = True

    st.text("")
    st.text("")
    st.text("")


def main_gui():
    current_action = None
    userinput = None

    if "--userinput" in sys.argv:
        userinput = sys.argv[sys.argv.index("--userinput") + 1]

    if "currentaction" not in st.session_state:
        st.session_state.currentaction = None

    with st.sidebar:
        st.title("HPCAdvisor")
        st.divider()

        button_newdeploy = st.button("Create Deployment", key="button_newdeploy")
        st.text("")

        button_viewdeploy = st.button("View Deployment", key="button_viewdeploy")
        st.text("")

        button_newcollect = st.button("Run Scenarios", key="button_newcollect")
        st.text("")

        button_newplot = st.button("View Plots", key="button_newplot")
        st.text("")

        button_newadvice = st.button("Get Advice", key="button_newadvice")
        st.divider()

    if (
        not button_newdeploy
        and not button_viewdeploy
        and not button_newcollect
        and not button_newplot
        and not button_newadvice
        and st.session_state.currentaction == None
    ):
        st.markdown("### HPC Resource Selection Advisor")
        st.text("")
        st.text("")
        st.write(" **What you can do**")
        st.text("🔸 Generate new data for better decision making")
        st.text("🔸 Explore existing data to get more insights yourself")
        st.text("🔸 Have advise from existing application")

    if button_newdeploy:
        st.session_state.currentaction = "create_deploy"
        create_deployment(userinput)
    elif button_viewdeploy:
        st.session_state.currentaction = "view_deploy"
        view_deployments()
    elif button_newcollect:
        st.session_state.currentaction = "create_collect"
        start_datacollection(userinput)
    elif button_newplot:
        st.session_state.currentaction = "create_plot"
        view_plot()
    elif button_newadvice:
        st.session_state.currentaction = "create_advice"
        view_advice()
    elif (
        "currentaction" in st.session_state
        and st.session_state.currentaction == "create_deploy"
    ):
        create_deployment(userinput)
    elif (
        "currentaction" in st.session_state
        and st.session_state.currentaction == "view_deploy"
    ):
        view_deployments()
    elif (
        "currentaction" in st.session_state
        and st.session_state.currentaction == "create_collect"
    ):
        start_datacollection(userinput)
    elif (
        "currentaction" in st.session_state
        and st.session_state.currentaction == "create_plot"
    ):
        view_plot()
    elif (
        "currentaction" in st.session_state
        and st.session_state.currentaction == "create_advice"
    ):
        view_advice()

    # remove streamlit bottom info
    hide_streamlit_style = """
            <style>
            # MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


if __name__ == "__main__":
    main_gui()


def main(debug, userinput):
    log.info("Starting HPC Advisor GUI")

    sys.argv = ["streamlit", "run", __file__]
    if userinput:
        sys.argv.append("--")
        sys.argv.append("--userinput")
        sys.argv.append(userinput)

    sys.exit(stcli.main())
