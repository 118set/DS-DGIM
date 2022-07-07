import csv
import streamlit as st
from dgim import Dgim
from datetime import datetime
from collections import Counter

# run with: streamlit run main.py

def main():
    data = prepare_data()

    st.subheader("Data subset")

    col1, col2 = st.columns(2)

    most_common_conditions = get_most_common_in_column(data, 'condition', 10)   

    condition = col1.selectbox("Condition", ['Any'] + most_common_conditions, index = 0)

    if condition != 'Any':
        data = [x for x in data if x['condition'] == condition]

    most_common_drugs = get_most_common_in_column(data, 'drugName', 5) 
   
    medication = col2.selectbox("Drug", ['Any'] + most_common_drugs, index = 0)

    if medication != 'Any':
        data = [x for x in data if x['drugName'] == medication]

    results = [0] * 10

    st.subheader("DGIM Params")
    col1, col2 = st.columns(2)

    window_size = col1.slider("Window Size", 16, len(data), 512)
    st_error_rate = col2.slider("Error Rate", 0.01, 0.5, 0.5, step=0.01)

    for d in data[-window_size:]:
        results[d['rating'] - 1] += 1

    dgims = [Dgim(N=window_size, error_rate=st_error_rate) for i in range(0, 10)]

    for el in data:
        for i in range(0, 10):
            dgims[i].update(el['rating_onehot'][i])

    draw_chart(results, [d.get_count() for d in dgims])

def draw_chart(results, dgim_res):
    chart_values = (
        [{"Rating": i + 1, "group": "Actual", "Amount": results[i] } for i in range(0, 10)] + 
        [{"Rating": i + 1, "group": "DGIM", "Amount": dgim_res[i] } for i in range(0, 10)]
    )
    
    st.subheader("Results")
    st.vega_lite_chart(None, {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {
                "values": chart_values
            },
            "mark": "bar",
            "encoding": {
                "x": {"field": "Rating"},
                "y": {"field": "Amount", "type": "quantitative"},
                "xOffset": {"field": "group"},
                "color": {"field": "group"}
            },
            "height": 300,
            "config": {
                "legend": {
                    # "orient": "bottom",
                    "title": None
                }
            }
        }, use_container_width=True)

@st.cache(hash_funcs={list: lambda _: None})
def prepare_data():
    tsv_file1 = open("./data/drugsComTrain_raw.tsv", encoding="utf-8")
    tsv_file2 = open("./data/drugsComTrain_raw.tsv", encoding="utf-8")

    read_tsv1 = csv.DictReader(tsv_file1, delimiter="\t")
    read_tsv2 = csv.DictReader(tsv_file2, delimiter="\t")

    data = list(read_tsv1) + list(read_tsv2)
    data = sort_by_date(data)
    onehot_encode(data)

    return data

def sort_by_date(data):
    for d in data:
        d['datetime'] = datetime.strptime(d['date'], "%B %d, %Y")

    return sorted(data, key=lambda d : d['datetime'])
    
def get_most_common_in_column(data, column, n):
    c = Counter([x[column] for x in data])
    most_common = [x[0] for x in c.most_common(n)]
    
    return most_common

def onehot_encode(data):
    for el in data:
        el['rating_onehot'] = [False] * 10
        rating = int(float(el['rating']))
        el['rating_onehot'][rating - 1] = True
        el['rating'] = rating

if __name__ == "__main__":
    main()