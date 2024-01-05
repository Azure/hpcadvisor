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

from hpcadvisor import (
    data_collector,
    dataset_handler,
    logger,
    plot_generator,
    task_generator,
    utils,
)

log = logger.logger

# TODO: this entire code needs to be refactored

tasks_filename = "tasks.txt"
execution_tracker_filename = "progress.txt"


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


current_dir = os.path.dirname(os.path.abspath(__file__))
style_css_path = os.path.join(current_dir, "./style.css")
local_css(style_css_path)

st.session_state["executionOn"] = False


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


def show_advise(current_goal, app):
    if current_goal == "Primary: Performance":
        return "hbv4/hx"
    if current_goal == "Primary: Cost":
        return "hbv2"
    else:
        return "hbv4, hbv3"


def disable(b):
    st.session_state["disabled"] = b


def show_recommendation(app):
    st.write("# Application: ", app)

    st.text("")
    st.text("")
    st.text("")
    st.markdown("### What are the application highlights?")
    with st.expander("Highlights"):
        st.markdown("###### - Memory intensive")
        st.markdown("###### - Tightly coupled: benefits from high-speed network")
        st.markdown("###### - Scale well until 100 VMs")

    st.text("")
    st.text("")
    st.text("")

    markdown_text = f"### What is your goal?"
    st.markdown(markdown_text)

    with st.expander("Setup goal"):
        goal = st.radio(
            "🔍 Select",
            [
                None,
                "Primary: Performance",
                "Primary: Cost",
                "Balance Performance and Cost",
            ],
            index=0,
        )

    current_goal = goal
    if current_goal is not None:
        st.text(current_goal)

    st.text("")
    st.text("")
    st.text("")

    st.markdown("### Resource selection advise ")

    with st.expander("More details"):
        st.markdown(
            "###### - Data available for the following SKUs: hbv4/hx, hbv3, hbv2"
        )
        st.markdown("###### - Common bottlenext: CPU and network")
        st.markdown("###### - Max # of VMs executed: 120")
        st.markdown("###### - Application input tested: conus 2.5km")
    possibilities = f"Possible SKUs: { show_advise(current_goal, app)}"
    st.markdown(possibilities)

    st.text("")
    st.text("")
    st.text("")


def show_plot_files(st, deployment_name):
    dataset_filename = utils.get_dataset_filename()

    if os.path.exists(dataset_filename):
        appinputs = dataset_handler.get_appinput_combinations(dataset_filename)
        for appinput in appinputs:
            plot_generator.gen_plot_exectime_vs_numvms(st, dataset_filename, appinput)
            plot_generator.gen_plot_exectime_vs_cost(st, dataset_filename, appinput)


def show_dataexploration(app):
    st.write("# Application: ", app)

    st.text("")
    st.text("")
    st.text("")

    st.markdown("### Data exploration ")
    with st.expander("Setup"):
        deployment_name = st.text_input(
            "Deployment",
            "",
            key="deployment_id",
        )

    genplots_button = st.button("Generate Plots")

    if genplots_button:
        with st.expander("data points"):
            show_plot_files(st, deployment_name)

    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")


def load_data_gen_defaults():
    data_gen_defaults = {}

    defaults_file = utils.get_ui_default_filename()

    if os.path.exists(defaults_file):
        with open(defaults_file) as f:
            data_gen_defaults = json.load(f)

    return data_gen_defaults


def _get_str(data):
    if isinstance(data, list):
        return ",".join(str(x) for x in data)
    else:
        return str(data)


def _get_defaults():
    defaults = {}
    data_gen_defaults = load_data_gen_defaults()

    for key in (
        "subscription",
        "region",
        "rgprefix",
        "skus",
        "nnodes",
        "ppr",
        "appsetupurl",
        "apprunscript",
    ):
        if key in data_gen_defaults:
            defaults[key] = _get_str(data_gen_defaults[key])
        else:
            defaults[key] = ""

    appinputs = ""
    if "appinputs" in data_gen_defaults:
        for key, value in data_gen_defaults["appinputs"].items():
            appinputs += f"{key.upper()}={_get_str(value)}\n"

    defaults["appinputs"] = appinputs

    if defaults["rgprefix"] == "":
        defaults["rgprefix"] = "hpcadvisor"

    return defaults


def _get_app_inputs(appinputs):
    data_app_input = {}
    for line in appinputs.splitlines():
        if line.strip():
            key, value = line.split("=")
            data_app_input[key] = value.split(",")

    return data_app_input


def show_datageneration(app):
    st.write("# Application: ", app)

    st.text("")
    st.text("")
    st.text("")

    defaults = _get_defaults()

    st.markdown("### Data generator ")
    task_filename = ""
    with st.expander("Setup"):
        text_subscription = st.text_input(
            "Azure subscription", defaults["subscription"]
        )
        text_region = st.text_input("Azure region", defaults["region"])
        text_skus = st.text_input("SKUs", defaults["skus"], key="field_sku")
        text_nnodes = st.text_input(
            "Number of nodes", defaults["nnodes"], key="field_nnodes"
        )
        text_ppr = st.text_input(
            "Processes per resource (%)", defaults["ppr"], key="field_ppr"
        )

        text_appinput = st.text_area(
            "Application input per line (<variable=value>)",
            defaults["appinputs"],
            key="app_info",
        )

        field_appsetup = st.text_input(
            "App setup script (git URL)",
            defaults["appsetupurl"],
            key="app_url_setup",
        )
        field_apprun = st.text_input(
            "App execution script in storage account",
            defaults["apprunscript"],
            key="app_url_run",
        )

        if "app_" in st.session_state and st.session_state.run_button == True:
            st.session_state.running = True
        else:
            st.session_state.running = False

        gentasks_key = "gentasks_button"

        # TODO: fix show/hide tasks button

        if gentasks_key not in st.session_state:
            st.session_state[gentasks_key] = False

        if st.session_state[gentasks_key]:
            rg_prefix = defaults["rgprefix"] + utils.get_random_code()
            st.session_state["rg_prefix"] = rg_prefix
            task_filename = utils.get_task_filename(rg_prefix)
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

            data = task_generator.generate_tasks(
                task_filename, data_system, data_app_input
            )

            df = pd.DataFrame(data)

            st.button("Hide Tasks")
            st.session_state[gentasks_key] = False
            df.index.name = "task"

            st.dataframe(df, height=200, width=700)

        else:
            gentasks_button = st.button("Show Tasks")
            st.session_state[gentasks_key] = True

        if (
            "run_datacollector_button" in st.session_state
            and st.session_state.run_datacollector_button == True
        ):
            st.session_state.running = True
        else:
            st.session_state.running = False

        if st.button(
            "START DATA COLLECTION",
            disabled=st.session_state.running,
            key="run_datacollector_button",
        ):
            execution_placeholder = st.empty()

            if st.session_state["executionOn"] == False:
                st.text("This will take a while. Please wait...")
                st.session_state["executionOn"] = True
                rg_prefix = st.session_state["rg_prefix"]
                user_data = {}
                user_data["subscription"] = text_subscription
                user_data["region"] = text_region
                user_data["rgprefix"] = rg_prefix
                user_data["skus"] = text_skus
                user_data["nnodes"] = text_nnodes
                user_data["ppr"] = text_ppr
                user_data["appinputs"] = text_appinput
                user_data["ppr"] = text_ppr
                user_data["appsetupurl"] = field_appsetup
                user_data["apprunscript"] = field_apprun

                data_system = {}
                data_system["sku"] = user_data["skus"].split(",")
                data_system["nnodes"] = user_data["nnodes"].split(",")
                data_system["ppr"] = user_data["ppr"].split(",")

                data_app_input = _get_app_inputs(user_data["appinputs"])

                env_file = utils.generate_env_file(rg_prefix, user_data)
                utils.execute_env_deployer(env_file, rg_prefix)

                task_filename = utils.get_task_filename(rg_prefix)
                task_generator.generate_tasks(
                    task_filename, data_system, data_app_input
                )
                log.info(f"task_filename={task_filename} generated for {rg_prefix}")

                dataset_filename = utils.get_dataset_filename()
                data_collector.collect_data(task_filename, dataset_filename, env_file)
                time.sleep(3.00)
                st.text("DONE.")

                log.info(f"finish execution for {rg_prefix}")

                st.success("Benchmark data generated successfully!")
                st.session_state.output = "output generated"
                st.rerun()

                if "output" in st.session_state:
                    st.success("Benchmark data generated successfully!")
                st.session_state["executionOn"] = False

    st.text("")
    st.text("")
    st.text("")


def main_gui():
    current_action = None
    if "currentaction" not in st.session_state:
        st.session_state.currentaction = None
    print("st.session_state=", st.session_state)

    with st.sidebar:
        st.title("⚙️  AzHPCAdvisor \n Azure HPC Resource Selection Advisor")
        st.text("")
        st.text("")
        st.text("")
        st.markdown("**APPLICATIONS**")

        newapp_clicked = st.button("New")

        # workaround to hide first selection in radio
        # https://discuss.streamlit.io/t/remove-the-preselection-of-radio-buttons/25702/4
        st.markdown(
            """
    <style>
        div[role=radiogroup] label:first-of-type {
            visibility: hidden;
            height: 0px;
        }
    </style>
    """,
            unsafe_allow_html=True,
        )

        app = st.radio(
            "🔍 Selection",
            [None, "MATRIX", "WRF", "GROMACS", "NAMD", "OPENFOAM"],
            index=0,
        )

        #######################################################################################
        st.write("Operations")

        disable_buttons = False
        if app == None:
            disable_buttons = True
        button_recommendation = st.button(
            "Recommendation",
            disabled=True,
            help="Discover the right infrastructure to run your application",
        )
        button_dataexploration = st.button(
            "Data Exploration",
            disabled=disable_buttons,
            help="Get more insights by understanding existing data",
        )
        button_datageneration = st.button(
            "Data Generation",
            disabled=disable_buttons,
            use_container_width=False,
            help="Generate more data to get better insights",
        )

    #######################################################################################

    if (
        not button_recommendation
        and not button_datageneration
        and not button_dataexploration
        and st.session_state.currentaction == None
    ):
        #  if not button_recommendation and not button_dataexploration and not button_datageneration:
        st.title("Welcome to the AzHPCAdvisor")
        st.text("")
        st.text("")
        st.write(" **What you can do**")
        st.text("🔸 Have advise from existing application")
        st.text("🔸 Explore existing data to get more insights yourself")
        st.text("🔸 Generate new data for better decision making")

    if app == "MATRIX" and button_recommendation:
        st.session_state.currentaction = "recommend"
        show_recommendation(app)

    if app == "MATRIX" and (
        button_dataexploration or st.session_state.currentaction == "dataexplore"
    ):
        st.session_state.currentaction = "dataexplore"
        if button_datageneration == False:
            show_dataexploration(app)

    if app == "MATRIX" and (
        button_datageneration or st.session_state.currentaction == "datagen"
    ):
        st.session_state.currentaction = "datagen"
        show_datageneration(app)

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


def main(debug):
    log.info("Starting HPC Advisor GUI")

    if debug:
        logger.setup_debug_mode()

    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())
