        if size_summary.empty:
            st.info('There are not enough historical transactions per size range to make a reliable comparison. Try selecting more months or towns.')
        else:
            # Sort size bands numerically and keep their order in the chart.
            size_order = (size_summary[['size_start', 'size_label']]
                          .drop_duplicates().sort_values('size_start')['size_label'].tolist())
            if HAS_PLOTLY:
                bar = px.bar(
                    size_summary,
                    x='size_label', y='median_price', color='flat_type',
                    barmode='group', category_orders={'size_label': size_order},
                    custom_data=['transactions'],
                    labels={'size_label': 'Home size (sqm)',
                            'median_price': 'Typical sold price (S$)',
                            'flat_type': 'Flat type'},
                    color_discrete_sequence=['#0C877B', '#2D6DA3', '#E5A252', '#7565A4', '#CF8077']
                )
                bar.update_traces(
                    hovertemplate='<b>%{x}</b><br>Median sold price: S$%{y:,.0f}<br>Historical transactions: %{customdata[0]:,}<extra>%{fullData.name}</extra>'
                )
                bar.update_yaxes(tickprefix='S$', tickformat=',.0f')
                bar.update_layout(hovermode='closest', bargap=.22)
                st.plotly_chart(base_chart(bar, 385), use_container_width=True)
            else:
                chart_table = (size_summary.pivot_table(
                    index='size_label', columns='flat_type', values='median_price', observed=True)
                    .reindex(size_order))
                st.bar_chart(chart_table, x_label='Home size (sqm)', y_label='Median resale price (S$)',
                             use_container_width=True)
            most_common = (size_summary.sort_values('transactions', ascending=False).iloc[0])
            st.info(
                f"**How to read this chart:** Compare the heights of the bars to see the typical resale price "
                f"for each home-size range. For example, {most_common['flat_type']} flats measuring "
                f"{most_common['size_label']} had a median sold price of "
                f"{cash(most_common['median_price'])} across "
                f"{int(most_common['transactions']):,} recorded transactions in this search. "
                "The chart uses completed historical sales, not current asking prices."
            )
            st.caption('Groups with fewer than 3 recorded transactions are excluded; each median is calculated from all matching transactions in the group. Prices may also reflect town, lease and storey differences.')
            with st.expander('Show sample sizes by home size'):
                st.dataframe(size_summary[['size_label','flat_type','transactions','median_price']].rename(
                    columns={'size_label':'Home size','flat_type':'Flat type','transactions':'Historical sales','median_price':'Median sold price (S$)'}),
                    hide_index=True, use_container_width=True)
        st.markdown('**Actual recorded transactions**')
        wanted=['month','town','flat_type','block','street_name','storey_range','floor_area_sqm','remaining_lease','resale_price','price_per_sqm']
        cols=[c for c in wanted if c in hist.columns]
        listing=hist[cols].sort_values('month',ascending=False).copy()
        listing['month']=listing['month'].dt.strftime('%Y-%m')
        st.dataframe(listing,hide_index=True,use_container_width=True,height=385)
        st.download_button('↓  Download these transactions (CSV)',data=listing.to_csv(index=False).encode('utf-8'),
            file_name='hdb_historical_transactions.csv',mime='text/csv')

with tabs[3]:
    st.markdown('<div class="sectionhead">Where the numbers come from</div><div class="sectionnote">Transparent methodology and pipeline diagnostics.</div>',unsafe_allow_html=True)
    st.markdown('Data source: Singapore Government HDB resale transactions, processed by your BA6003 group pipeline. Monthly medians describe transactions registered during the relevant month, not asking prices.')
    st.markdown('**Interpretation:** A percentage within budget means historical sales at or below that amount; it does not mean that percentage of current listings is available. These analyses are indicative, not an official property valuation.')
    if REPORT.exists():
        try:
            report=json.loads(REPORT.read_text(encoding='utf-8'))
            q1,q2,q3,q4=st.columns(4)
            q1.metric('Raw rows',f"{report.get('raw_rows',0):,}")
            q2.metric('Processed rows',f"{report.get('clean_rows',0):,}")
            q3.metric('Property matched',f"{report.get('property_match_rate',0)*100:.2f}%")
            q4.metric('Flagged records',f"{report.get('quality_issues',0):,}")
            st.caption(f"Date range: {report.get('date_min','—')} to {report.get('date_max','—')} · Duplicate rows flagged: {report.get('duplicates','—')}")
        except (OSError,ValueError,TypeError) as exc:
            st.warning(f'Unable to read quality report: {exc}')
    else:
        st.info('quality_report.json is not available. Run the full pipeline to generate it.')

with tabs[4]:
    st.markdown('<div class="sectionhead">Ask HDB Atlas AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sectionnote">Ask which towns have more past sales in your budget, or request historical price ranges by town and flat type.</div>', unsafe_allow_html=True)
    ai_context = build_ai_context(
        view, aff, recent, mode, selected_types, budget, period, max_month
    )
    current_filter_key = json.dumps(ai_context, sort_keys=True)
    if st.session_state.get("hdb_chat_filter_key") != current_filter_key:
        st.session_state["hdb_chat_filter_key"] = current_filter_key
        st.session_state["hdb_chat_messages"] = []
    if "hdb_chat_messages" not in st.session_state:
        st.session_state["hdb_chat_messages"] = []

    st.info("This assistant uses historical HDB transaction summaries, not live property listings. Change filters above to change its data context.")
    if st.button("Clear conversation", key="clear_hdb_ai_chat"):
        st.session_state["hdb_chat_messages"] = []

    for message in st.session_state["hdb_chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("E.g. Which towns have more 4-room sales within my budget?", key="hdb_ai_input")
    if question:
        st.session_state["hdb_chat_messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Analysing the selected HDB data..."):
                try:
                    answer = ask_hdb_ai(st.session_state["hdb_chat_messages"], ai_context)
                    st.markdown(answer)
                    st.session_state["hdb_chat_messages"].append({"role": "assistant", "content": answer})
                except RuntimeError as exc:
                    st.error(str(exc))
                    # A failed call should not contaminate the next conversation turn.
                    st.session_state["hdb_chat_messages"].pop()
    st.caption("AI text may contain errors. Verify important decisions against official HDB sources.")

st.markdown('<div class="smallfooter"><span>© HDB ATLAS &nbsp;·&nbsp; BA6003 GROUP PROJECT</span><span>Built for better decisions &nbsp;·&nbsp; Historical analytics, not an official valuation</span></div>',unsafe_allow_html=True)
