"""
Gemini provider card
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .base_card import BaseProviderCard

logger = logging.getLogger(__name__)


class GeminiCard(BaseProviderCard):
    """Card for Google Gemini provider"""
    
    def __init__(self):
        super().__init__(
            provider_name="gemini",
            display_name="Gemini",
            color="#2196f3",  # Bright blue
            size=(220, 104)  # Half-height
        )
        self.api_key = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        
    def setup_content(self):
        """Add Gemini-specific content"""
        # Cost display
        self.cost_label = QLabel("$0.0000")
        self.cost_label.setTextFormat(Qt.TextFormat.RichText)
        font = QFont()
        font.setPointSize(self.base_font_sizes['secondary'])  # Smaller font for half-height
        self.cost_label.setFont(font)
        self.cost_label.setStyleSheet(" font-weight: bold;")
        self.layout.addWidget(self.cost_label)
        
        # Requests display
        self.requests_label = QLabel("Requests: -")
        self.requests_label.setTextFormat(Qt.TextFormat.RichText)
        self.requests_label.setStyleSheet(f" font-size: {self.base_font_sizes['secondary']}px;")
        self.layout.addWidget(self.requests_label)
        
    def update_display(self, data: Dict[str, Any]):
        """Update the card with new data"""
        cost = data.get('cost', 0.0)
        requests = data.get('requests', 0)
        status = data.get('status', 'Active')
        status_type = data.get('status_type', 'normal')
        
        # Update cost with estimated label
        self.cost_label.setText(
            f'${cost:.4f} <span style="font-size: {self.base_font_sizes["small"]}px; '
            f'color: #888; font-weight: normal;">(Estimated)</span>'
        )
        
        # Update requests with exact label
        if requests >= 0:
            self.requests_label.setText(
                f'Requests: {requests:,} <span style="font-size: '
                f'{self.base_font_sizes["small"]}px; color: #888;">(Exact)</span>'
            )
        else:
            self.requests_label.setText("Requests: -")
            
        # Update status
        self.update_status(status, status_type)
        
    def scale_content_fonts(self, scale: float):
        """Scale the content fonts"""
        # Scale cost label
        font = QFont()
        font.setPointSize(int(self.base_font_sizes['secondary'] * scale))
        self.cost_label.setFont(font)
        
        # Scale requests label
        self.requests_label.setStyleSheet(
            f" font-size: {int(self.base_font_sizes['secondary'] * scale)}px;"
        )
        
        # Update rich text with new sizes
        cost_text = self.cost_label.text()
        if "(Estimated)" in cost_text:
            # Extract the cost value
            cost_value = cost_text.split(' <span')[0]
            self.cost_label.setText(
                f'{cost_value} <span style="font-size: {int(self.base_font_sizes["small"] * scale)}px; '
                f'color: #888; font-weight: normal;">(Estimated)</span>'
            )
            
        requests_text = self.requests_label.text()
        if "(Exact)" in requests_text:
            # Extract the requests value
            parts = requests_text.split(' <span')
            if len(parts) > 1:
                requests_value = parts[0]
                self.requests_label.setText(
                    f'{requests_value} <span style="font-size: '
                    f'{int(self.base_font_sizes["small"] * scale)}px; color: #888;">(Exact)</span>'
                )
                
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch Gemini usage data"""
        if not self.api_key:
            return {
                'cost': 0.0,
                'requests': 0,
                'status': 'No API key',
                'status_type': 'error'
            }
            
        try:
            # Import Google Cloud libraries
            try:
                from google.cloud import monitoring_v3
                import google.auth
            except ImportError:
                logger.error("Google Cloud packages not installed")
                return {
                    'cost': 0.0,
                    'requests': 0,
                    'status': 'Missing dependencies',
                    'status_type': 'error'
                }
                
            # Get credentials
            try:
                credentials, _ = google.auth.default()
            except Exception:
                return {
                    'cost': 0.0,
                    'requests': 0,
                    'status': 'Auth failed',
                    'status_type': 'error'
                }
                
            # Use monitoring API for request counts
            monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)
            
            project_name = f"projects/{self.api_key}"
            interval = monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": int(datetime.now().timestamp())},
                    "start_time": {"seconds": int((datetime.now() - timedelta(hours=24)).timestamp())},
                }
            )
            
            # Query for Vertex AI requests - need separate queries due to API restrictions
            total_requests = 0
            
            # Query online predictions
            try:
                results = monitoring_client.list_time_series(
                    request={
                        "name": project_name,
                        "filter": 'metric.type="aiplatform.googleapis.com/prediction/online/request_count"',
                        "interval": interval,
                    }
                )
                
                gemini_models = ["gemini", "text-bison", "chat-bison"]
                for result in results:
                    resource_labels = result.resource.labels
                    model_id = resource_labels.get("model_id", "").lower()
                    
                    if model_id:
                        logger.debug(f"Found Vertex AI model: {model_id}")
                        
                    if any(gemini_model in model_id for gemini_model in gemini_models) or not model_id:
                        for point in result.points:
                            total_requests += point.value.int64_value
            except Exception:
                pass
                
            # Query model predictions
            try:
                results = monitoring_client.list_time_series(
                    request={
                        "name": project_name,
                        "filter": 'metric.type="aiplatform.googleapis.com/prediction/model/request_count"',
                        "interval": interval,
                    }
                )
                
                for result in results:
                    resource_labels = result.resource.labels
                    model_id = resource_labels.get("model_id", "").lower()
                    
                    if model_id:
                        logger.debug(f"Found Vertex AI model: {model_id}")
                        
                    if any(gemini_model in model_id for gemini_model in gemini_models) or not model_id:
                        for point in result.points:
                            total_requests += point.value.int64_value
            except Exception:
                pass
                        
            # Estimate cost
            estimated_cost_per_request = 0.0025 + (0.01 * 2)
            estimated_daily_cost = total_requests * estimated_cost_per_request
            
            logger.info(f"Gemini: {total_requests} requests, estimated ${estimated_daily_cost:.2f}")
            
            return {
                'cost': estimated_daily_cost,
                'requests': total_requests,
                'status': 'Active' if estimated_daily_cost > 0 else 'Updates are not in real time',
                'status_type': 'normal' if estimated_daily_cost > 0 else 'italic'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Gemini data: {e}")
            return {
                'cost': 0.0,
                'requests': 0,
                'status': 'Error',
                'status_type': 'error'
            }