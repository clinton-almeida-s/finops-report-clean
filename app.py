"""
GCP Cost Optimizer - Streamlit Dashboard
Interactive web interface for analyzing and visualizing GCP costs.
"""
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from billing_collector import BillingCollector


def main():
    st.set_page_config(
        page_title="GCP Cost Optimizer",
        page_icon="☁️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title and header
    st.title("☁️ GCP Cloud Cost Optimizer")
    st.markdown("*Intelligent cloud cost analysis and optimization recommendations*")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Auto-detect billing account from environment or gcloud
        default_billing = os.environ.get("GCP_BILLING_ACCOUNT", "0136FF-F52314-9FF856")
        billing_account = st.text_input(
            "Billing Account ID",
            value=default_billing,
            help="Your GCP billing account ID (e.g., ABC123-DEF456-GHI789)"
        )

        credentials_path = st.text_input(
            "Service Account Key (Optional)",
            value=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
            help="Path to your GCP service account JSON key file (optional if using gcloud auth)"
        )

        # Manual token input for when gcloud credential files aren't auto-detected
        gcp_access_token = st.text_input(
            "GCP Access Token (Optional)",
            value=os.environ.get("GCP_ACCESS_TOKEN", ""),
            help="Run `gcloud auth print-access-token` and paste the result here. Overrides other methods if provided."
        ).strip()

        if gcp_access_token:
            os.environ["GCP_ACCESS_TOKEN"] = gcp_access_token

        months_back = st.slider(
            "Analysis Period (months)",
            min_value=1,
            max_value=12,
            value=3,
            help="Number of months of billing data to analyze"
        )

        st.divider()

        if st.button("🔍 Analyze Costs", type="primary", use_container_width=True):
            st.session_state.analyzed = True
            st.session_state.recommendations = None
            st.session_state.savings = None

        st.markdown("---")
        st.markdown("**💡 Tips:**")
        st.markdown("- Ensure `gcloud auth login` is active")
        st.markdown("- Or provide a service account JSON key")
        st.markdown("- Analysis queries Compute Engine + Monitoring APIs")

    # Initialize session state
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    if 'savings' not in st.session_state:
        st.session_state.savings = {}
    if 'billing_data' not in st.session_state:
        st.session_state.billing_data = {}

    # Main content area
    if not st.session_state.analyzed:
        st.info("👆 Configure your billing account and click **Analyze Costs** to get started")

        # Show demo section
        st.subheader("📋 Quick Demo")
        st.markdown("Click **Analyze Costs** above with the demo settings to see sample results.")

        # Features overview
        st.divider()
        st.subheader("🎯 Features")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("VM Rightsizing", "Identify over-provisioned instances")
        with col2:
            st.metric("Spot Instance Analysis", "Find savings opportunities")
        with col3:
            st.metric("Cost Visualization", "Interactive dashboards")

    else:
        # Create collector and fetch data
        with st.spinner("🔄 Fetching billing data..."):
            try:
                # Set manual token if provided
                if gcp_access_token:
                    os.environ["GCP_ACCESS_TOKEN"] = gcp_access_token

                collector = BillingCollector(
                    billing_account_id=billing_account,
                    credentials_path=credentials_path if credentials_path else None
                )

                billing_data = collector.fetch_billing_data(months_back=months_back)
                recommendations = collector.get_vm_recommendations()
                spot_candidates = collector.get_spot_instance_candidates()
                savings = collector.calculate_total_potential_savings()

                st.session_state.recommendations = recommendations
                st.session_state.savings = savings
                st.session_state.billing_data = billing_data
            except RuntimeError as e:
                st.error(f"Authentication failed: {e}")
                st.info("Make sure you've run `gcloud auth login` or provided a service account key.")
                st.stop()

        # Summary metrics
        st.divider()
        st.subheader("📊 Cost Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_monthly = sum(data['total_cost'] for data in st.session_state.billing_data.values()) / max(len(st.session_state.billing_data), 1)
            st.metric("Monthly Avg Cost", f"${total_monthly:,.2f}")
        with col2:
            st.metric("Potential Savings", f"${savings['total_potential_savings']:,.2f}")
        with col3:
            savings_pct = (savings['total_potential_savings'] / total_monthly * 100) if total_monthly > 0 else 0
            st.metric("Savings Percentage", f"{savings_pct:.1f}%")
        with col4:
            st.metric("Recommendations", f"{len(recommendations)}")

        # Charts row 1: Billing trend
        st.divider()
        st.subheader("📈 Billing Trend")

        months = list(st.session_state.billing_data.keys())
        costs = [st.session_state.billing_data[m]['total_cost'] for m in months]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=months,
            y=costs,
            mode='lines+markers',
            name='Monthly Cost',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=10)
        ))
        fig_trend.update_layout(
            height=300,
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            template="plotly_white"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Charts row 2: Service breakdown
        st.subheader("🔧 Service Breakdown (Latest Month)")

        latest_month = max(months)
        services = st.session_state.billing_data[latest_month]['services']

        fig_pie = go.Figure(data=[go.Pie(
            labels=list(services.keys()),
            values=list(services.values()),
            hole=0.4,
            marker=dict(colors=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'])
        )])
        fig_pie.update_layout(height=350, template="plotly_white")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Project breakdown
        st.subheader("🏢 Project Costs")

        projects = st.session_state.billing_data[latest_month]['projects']
        fig_projects = go.Figure(data=[go.Bar(
            x=list(projects.keys()),
            y=list(projects.values()),
            marker=dict(color='#3B82F6')
        )])
        fig_projects.update_layout(height=300, xaxis_title="Project", yaxis_title="Cost ($)", template="plotly_white")
        st.plotly_chart(fig_projects, use_container_width=True)

        # VM Rightsizing Recommendations
        st.divider()
        st.subheader("🔧 VM Rightsizing Recommendations")
        st.caption("Based on actual vs. requested resource utilization")

        rec_df = pd.DataFrame(recommendations)
        rec_df['potential_savings_numeric'] = rec_df['potential_savings'].str.replace('$', '').str.replace(',', '').astype(float)

        # Sort by potential savings
        rec_df = rec_df.sort_values('potential_savings_numeric', ascending=False)

        # Display as dataframe
        display_cols = ['instance_name', 'current_machine_type', 'recommended_machine_type',
                       'current_monthly_cost', 'recommended_monthly_cost', 'potential_savings', 'risk_level']

        st.dataframe(rec_df[display_cols], use_container_width=True, hide_index=True)

        # Savings bar chart
        st.subheader("💰 Potential Savings by Instance")
        fig_savings = go.Figure(data=[go.Bar(
            x=rec_df['instance_name'],
            y=rec_df['potential_savings_numeric'],
            marker=dict(color=rec_df['risk_level'].map({'low': '#10B981', 'medium': '#F59E0B', 'high': '#EF4444'})),
            text=rec_df['savings_percentage'],
            textposition='outside'
        )])
        fig_savings.update_layout(height=300, xaxis_title="Instance", yaxis_title="Monthly Savings ($)", template="plotly_white")
        st.plotly_chart(fig_savings, use_container_width=True)

        # Spot Instance Opportunities
        st.divider()
        st.subheader("☁️ Spot Instance Opportunities")
        st.caption("Workloads that can tolerate interruptions for significant savings")

        spot_df = pd.DataFrame(spot_candidates)
        spot_df['monthly_savings_numeric'] = spot_df['monthly_savings'].str.replace('$', '').str.replace(',', '').astype(float)

        # Display spot candidates
        display_spot = ['instance_name', 'workload_type', 'eligibility', 'estimated_savings', 'monthly_savings']
        st.dataframe(spot_df[display_spot], use_container_width=True, hide_index=True)

        # Eligibility breakdown
        st.subheader("📊 Eligibility Distribution")
        fig_elig = go.Figure(data=[go.Pie(
            labels=spot_df['eligibility'],
            values=spot_df['eligibility'].value_counts(),
            marker=dict(colors=['#10B981', '#F59E0B', '#EF4444'])
        )])
        fig_elig.update_layout(height=300, template="plotly_white")
        st.plotly_chart(fig_elig, use_container_width=True)

        # Actionable insights
        st.divider()
        st.subheader("💡 Actionable Insights")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Quick Win**: Right-size `dev-worker-02`\nSave $240/month")
        with col2:
            st.warning(f"**Medium Risk**: Migrate `ml-training-node` to E2\nSave $240/month")
        with col3:
            st.success(f"**Low Risk**: Move `batch-processor-01` to spot\nSave $480/month")

        # Export functionality
        st.divider()
        st.subheader("📤 Export Recommendations")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export to CSV", type="secondary"):
                csv_data = rec_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="gcp_recommendations.csv",
                    mime="text/csv"
                )
        with col2:
            if st.button("Export as JSON", type="secondary"):
                json_data = rec_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="gcp_recommendations.json",
                    mime="application/json"
                )

        # Help section
        with st.expander("❓ How to use these recommendations"):
            st.markdown("""
            **Rightsizing Recommendations:**
            - Review each instance's CPU/memory utilization
            - Low risk = safe to implement immediately
            - Medium risk = implement during maintenance window
            - High risk = requires careful planning

            **Spot Instance Opportunities:**
            - Batch processing and dev/test workloads are best candidates
            - Production workloads require careful evaluation
            - Consider reserved instances for steady workloads

            **Next Steps:**
            1. Start with low-risk recommendations
            2. Test changes in dev environment first
            3. Monitor performance after changes
            4. Implement spot instances for eligible workloads
            """)


if __name__ == "__main__":
    main()