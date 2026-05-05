import polars as pl
import plotly.graph_objects as go
import plotly.express as px
from data_wranglers.titanic_wrangler import TitanicWrangler


class TitanicChartingHelper:
    """Simple prototype for creating boxplots with survival-colored points."""
    
    # Constants - all styling options as fixed values
    POINT_SIZE = 6
    BOX_OPACITY = 0.7
    POINT_OPACITY = 0.6
    WIDTH = 800
    HEIGHT = 600
    SURVIVAL_COLORS = {'survived': '#2E8B57', 'died': '#DC143C'}  # Green, Red
    
    @staticmethod
    def create_strip_boxplot(data: pl.DataFrame, x_axis: str, y_axis: str) -> go.Figure:
        """
        Create boxplot with survival-colored points.
        
        Parameters:
        -----------
        data : pl.DataFrame
            Input data (must include 'Survived' column)
        x_axis : str
            Categorical variable for X-axis
        y_axis : str
            Continuous variable for Y-axis
            
        Returns:
        --------
        go.Figure
            Interactive Plotly figure with survival-colored points
        """
        
        # Clean data
        clean_data = data.filter(
            pl.col(y_axis).is_not_null() & 
            pl.col(x_axis).is_not_null() &
            pl.col('Survived').is_not_null()
        )
        
        # Calculate survival rates using TitanicWrangler method
        survival_stats = TitanicWrangler.calculate_survival_rate(clean_data, x_axis)
        
        # Create dictionaries for quick lookup
        category_counts = survival_stats.select("Category", "TotalCount").to_dict(as_series=False)
        category_counts = dict(zip(category_counts["Category"], category_counts["TotalCount"]))
        
        survival_rates = survival_stats.select("Category", "SurvivalRate").to_dict(as_series=False)
        survival_rates = dict(zip(survival_rates["Category"], survival_rates["SurvivalRate"]))
        
        # Create strip plot using plotly express with stripmode for jittering
        fig = px.strip(
            clean_data, 
            x=x_axis, 
            y=y_axis,
            color='Survived',
            color_discrete_map={'Survived': TitanicChartingHelper.SURVIVAL_COLORS['survived'], 
                               'Died': TitanicChartingHelper.SURVIVAL_COLORS['died']},
            stripmode='overlay',  # This overlays/jitters the points horizontally
            hover_data={'Name': True, 'Sex': True, 'Age': True, 'Pclass': True, 'Embarked': True, x_axis: False, y_axis: False}
        )
        
        # Update marker properties and hover template for strip plot traces
        # px.strip creates Box traces that display as strip plots with markers
        for trace in fig.data:
            if hasattr(trace, 'marker'):  # This is a strip plot trace with markers
                trace.marker.size = TitanicChartingHelper.POINT_SIZE
                trace.marker.opacity = TitanicChartingHelper.POINT_OPACITY
                trace.marker.line = dict(width=0.5, color='white')
        
        # Add box plots on top using Polars data
        unique_categories = clean_data[x_axis].unique().sort()
        for x_val in unique_categories:
            subset = clean_data.filter(pl.col(x_axis) == x_val)
            subset_y_values = subset[y_axis].to_list()
            fig.add_trace(go.Box(
                x=[x_val] * len(subset_y_values),
                y=subset_y_values,
                boxpoints=False,
                fillcolor='rgba(211,211,211,0.3)',  # Light grey with transparency
                line=dict(color='black', width=1.5),
                showlegend=False,
                hoverinfo='skip'  # Disable hover for box plots
            ))
        
        # Create x-axis tick labels with counts and survival rates using Polars data
        unique_categories_for_labels = clean_data[x_axis].unique().sort().to_list()
        tick_labels = [f"{cat}<br>(N={category_counts[cat]}, S={survival_rates[cat]:.1f}%)" for cat in unique_categories_for_labels]
        
        # Update layout
        fig.update_layout(
            title=f"{TitanicChartingHelper._format_axis_title(y_axis)} by {TitanicChartingHelper._format_axis_title(x_axis)}",
            xaxis_title=TitanicChartingHelper._format_axis_title(x_axis),
            yaxis_title=TitanicChartingHelper._format_axis_title(y_axis),
            width=TitanicChartingHelper.WIDTH,
            height=TitanicChartingHelper.HEIGHT,
            template="plotly_white",
            xaxis=dict(
                tickmode='array',
                tickvals=unique_categories_for_labels,
                ticktext=tick_labels
            )
        )
        
        return fig
    
    
    @staticmethod
    def _get_survival_color(survived: str) -> str:
        """Get color based on survival status."""
        return TitanicChartingHelper.SURVIVAL_COLORS['survived'] if survived == 'Survived' else TitanicChartingHelper.SURVIVAL_COLORS['died']
    
    @staticmethod
    def _format_axis_title(column_name: str) -> str:
        """Format column names for better axis labels."""
        formatting_map = {
            'Fare': 'Fare ($)',
            'Age': 'Age (years)',
            'FareLog10': 'Fare (log₁₀)',
            'Sex': 'Gender',
            'Level': 'Cabin Level',
            'AgeInDecades': 'Age (decades)',
            'Title': 'Title',
            'Embarked': 'Port of Embarkation',
            'Pclass': 'Passenger Class',
            'Survived': 'Survived'
        }
        return formatting_map.get(column_name, column_name)
    
