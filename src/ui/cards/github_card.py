"""
GitHub activity card
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from .base_card import BaseProviderCard
try:
    from ...utils.credentials import CredentialManager
except ImportError:
    # Fallback if credentials module not available
    CredentialManager = None

logger = logging.getLogger(__name__)


class ContributionHeatmap(QWidget):
    """Mini heatmap showing last 2 months of contributions"""
    
    def __init__(self):
        super().__init__()
        self.contributions = {}  # date -> count
        self.setFixedHeight(80)  # Proper height to show all 7 days with margin
        self.setMinimumWidth(195)  # Further reduced to fit within card borders
        self.theme_colors = {
            'background': QColor(255, 255, 255),
            'text': QColor(100, 100, 100),
            'empty': QColor(234, 234, 234),
            'level1': QColor(198, 228, 139),
            'level2': QColor(123, 201, 111),
            'level3': QColor(35, 154, 59),
            'level4': QColor(25, 97, 39)
        }
        
    def set_data(self, contributions: Dict[str, int]):
        """Set contribution data"""
        self.contributions = contributions
        # Log some sample data to debug
        if contributions:
            sample = list(contributions.items())[:5]
            logger.info(f"Heatmap data sample: {sample}, total days: {len(contributions)}")
        else:
            logger.warning("No contribution data provided to heatmap")
        self.update()
        
    def paintEvent(self, event):
        """Paint the heatmap"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use theme background
        painter.fillRect(self.rect(), self.theme_colors['background'])
        
        # Cell size
        cell_size = 8
        cell_spacing = 1
        
        # Calculate grid dimensions
        today = datetime.now().date()
        
        # Start from Sunday of 16 weeks ago (4 months)
        days_back = 112  # 16 weeks
        start_date = today - timedelta(days=days_back)
        # Adjust to previous Sunday
        days_since_sunday = start_date.weekday()
        if days_since_sunday != 6:  # If not Sunday
            start_date = start_date - timedelta(days=(days_since_sunday + 1) % 7)
        
        # Calculate total weeks from start to today
        total_days = (today - start_date).days + 1
        total_weeks = (total_days + 6) // 7
        
        # Calculate grid position with space for day labels
        grid_width = total_weeks * (cell_size + cell_spacing)
        day_label_width = 25  # Space for day labels
        start_x = day_label_width + 5  # Start after day labels
        start_y = 15  # Space for month labels
        
        # Draw day labels (Mon, Wed, Fri)
        painter.setFont(QFont("Arial", 8))
        painter.setPen(self.theme_colors['text'])
        
        # Monday (row 1)
        painter.drawText(5, start_y + 1 * (cell_size + cell_spacing) + 6, "Mon")
        # Wednesday (row 3)
        painter.drawText(5, start_y + 3 * (cell_size + cell_spacing) + 6, "Wed")
        # Friday (row 5)
        painter.drawText(5, start_y + 5 * (cell_size + cell_spacing) + 6, "Fri")
        
        # Draw month labels
        painter.setFont(QFont("Arial", 10))
        painter.setPen(self.theme_colors['text'])
        
        # Track months as we iterate - only show first occurrence
        current_month = None
        month_positions = []
        last_month_x = -50  # Track last position to avoid overlap
        
        # Draw the heatmap grid (column by column, like GitHub)
        for week_offset in range(total_weeks):
            week_start = start_date + timedelta(weeks=week_offset)
            
            # Track month label positions - ensure spacing
            if week_start.month != current_month:
                current_month = week_start.month
                x_pos = start_x + week_offset * (cell_size + cell_spacing)
                # Only add if there's enough space from last label
                if x_pos - last_month_x > 30:
                    month_positions.append((x_pos, week_start.strftime("%b")))
                    last_month_x = x_pos
            
            # Draw each day in the week (Sunday to Saturday)
            for day_of_week in range(7):
                date = week_start + timedelta(days=day_of_week)
                
                # Skip future dates
                if date > today:
                    continue
                    
                date_str = date.strftime("%Y-%m-%d")
                count = self.contributions.get(date_str, 0)
                
                # Calculate position
                x = start_x + week_offset * (cell_size + cell_spacing)
                y = start_y + day_of_week * (cell_size + cell_spacing)
                
                # Use theme colors
                if count == 0:
                    color = self.theme_colors['empty']
                elif count <= 3:
                    color = self.theme_colors['level1']
                elif count <= 6:
                    color = self.theme_colors['level2']
                elif count <= 9:
                    color = self.theme_colors['level3']
                else:
                    color = self.theme_colors['level4']
                    
                painter.fillRect(x, y, cell_size, cell_size, color)
                
        # Draw month labels
        for x_pos, month_name in month_positions:
            painter.drawText(x_pos, 12, month_name)


class GitHubCard(BaseProviderCard):
    """Card for GitHub activity monitoring"""
    
    def __init__(self):
        super().__init__(
            provider_name="github",
            display_name="GitHub",
            color="#673ab7",  # Deep purple
            size=(220, 210),  # Back to standard width
            show_status=False  # Don't show the status text since we display commits in title
        )
        # Use secure credential manager if available, fall back to env vars
        if CredentialManager:
            self.token = CredentialManager.get_credential("github", "token", "GITHUB_TOKEN")
            self.username = CredentialManager.get_credential("github", "username", "GITHUB_USERNAME")
        else:
            self.token = os.getenv("GITHUB_TOKEN", "")
            self.username = os.getenv("GITHUB_USERNAME", "")
            
    def update_theme_colors(self, is_dark: bool):
        """Update heatmap colors based on theme"""
        if is_dark:
            # Get the parent window to access theme manager
            parent = self.window()
            if parent and hasattr(parent, 'theme_manager'):
                # Use the card background color from the theme
                card_bg = parent.theme_manager.get_color('card_background')
                # Parse the color string to create QColor
                bg_color = QColor(card_bg)
            else:
                bg_color = QColor(30, 30, 30)
                
            self.heatmap.theme_colors = {
                'background': bg_color,
                'text': QColor(180, 180, 180),
                'empty': QColor(50, 50, 50),
                'level1': QColor(14, 68, 41),
                'level2': QColor(0, 109, 50),
                'level3': QColor(38, 166, 65),
                'level4': QColor(57, 211, 83)
            }
        else:
            self.heatmap.theme_colors = {
                'background': QColor(255, 255, 255),
                'text': QColor(100, 100, 100),
                'empty': QColor(234, 234, 234),
                'level1': QColor(198, 228, 139),
                'level2': QColor(123, 201, 111),
                'level3': QColor(35, 154, 59),
                'level4': QColor(25, 97, 39)
            }
        self.heatmap.update()
        
    def setup_content(self):
        """Add GitHub-specific content"""
        # Today's contributions
        self.contributions_label = QLabel("Today: -")
        font = QFont()
        font.setPointSize(self.base_font_sizes['title'] - 1)  # 1pt smaller than title
        font.setBold(True)
        self.contributions_label.setFont(font)
        # Color will be set by theme
        self.layout.addWidget(self.contributions_label)
        
        # Contribution heatmap
        self.heatmap = ContributionHeatmap()
        self.layout.addWidget(self.heatmap)
        
        # Add spacing before stats
        self.layout.addSpacing(10)
        
        # Stats row
        self.stats_widget = QWidget()
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(10)
        
        self.prs_label = QLabel("PRs: -")
        self.prs_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px;")
        stats_layout.addWidget(self.prs_label)
        
        self.issues_label = QLabel("Issues: -")
        self.issues_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px;")
        stats_layout.addWidget(self.issues_label)
        
        self.notifs_label = QLabel("Notifs: -")
        self.notifs_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px;")
        stats_layout.addWidget(self.notifs_label)
        
        stats_layout.addStretch()
        self.stats_widget.setLayout(stats_layout)
        self.layout.addWidget(self.stats_widget)
        
        # Recent commits
        self.recent_label = QLabel("Recent:")
        self.recent_label.setStyleSheet(f" font-size: {self.base_font_sizes['small']}px; margin-top: 5px;")
        self.layout.addWidget(self.recent_label)
        
        self.commit1_label = QLabel("...")
        self.commit1_label.setStyleSheet(f" font-size: {self.base_font_sizes['small'] - 1}px;")
        self.layout.addWidget(self.commit1_label)
        
        self.commit2_label = QLabel("...")
        self.commit2_label.setStyleSheet(f" font-size: {self.base_font_sizes['small'] - 1}px;")
        self.layout.addWidget(self.commit2_label)
        
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch GitHub data"""
        if not self.token:
            return {
                'status': 'No token',
                'status_type': 'error',
                'contributions_today': 0,
                'contributions_map': {},
                'open_prs': 0,
                'open_issues': 0,
                'notifications': 0,
                'recent_commits': [],
                'error_message': 'Set GITHUB_TOKEN with read:user scope'
            }
            
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            # Get user info if username not set
            if not self.username:
                user_resp = requests.get('https://api.github.com/user', headers=headers)
                if user_resp.status_code == 200:
                    self.username = user_resp.json()['login']
                    
            data = {
                'status': 'Connected',
                'status_type': 'normal',
                'contributions_today': 0,
                'contributions_map': {},
                'open_prs': 0,
                'open_issues': 0, 
                'notifications': 0,
                'recent_commits': []
            }
            
            # Get events data first (needed for recent commits)
            events = []
            try:
                events_resp = requests.get(
                    f'https://api.github.com/users/{self.username}/events',
                    headers=headers,
                    params={'per_page': 30}
                )
                if events_resp.status_code == 200:
                    events = events_resp.json()
                    # Debug: log recent push events
                    push_events = [e for e in events if e['type'] == 'PushEvent']
                    if push_events:
                        recent_repos = [e['repo']['name'] for e in push_events[:5]]
                        logger.debug(f"Recent push events from repos: {recent_repos}")
            except Exception as e:
                logger.error(f"Error fetching events: {e}")
            
            # Get contribution data using GraphQL
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Initialize contribution map
            contribution_map = {}
            
            # Calculate date range for contributions (last ~4 months)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=120)
            
            # Format dates for GraphQL (ISO 8601)
            from_date = start_date.strftime("%Y-%m-%dT00:00:00Z")
            to_date = end_date.strftime("%Y-%m-%dT23:59:59Z")
            
            # Try GraphQL API for contribution data
            graphql_query = '''
            query($userName: String!, $from: DateTime!, $to: DateTime!) {
                user(login: $userName) {
                    contributionsCollection(from: $from, to: $to) {
                        contributionCalendar {
                            totalContributions
                            weeks {
                                contributionDays {
                                    contributionCount
                                    date
                                    color
                                }
                            }
                        }
                    }
                }
            }
            '''
            
            graphql_resp = requests.post(
                'https://api.github.com/graphql',
                headers=headers,
                json={
                    'query': graphql_query,
                    'variables': {
                        'userName': self.username,
                        'from': from_date,
                        'to': to_date
                    }
                }
            )
            
            if graphql_resp.status_code == 200:
                graphql_data = graphql_resp.json()
                logger.info(f"GraphQL response: {graphql_resp.status_code}")
                
                if 'errors' in graphql_data:
                    logger.error(f"GraphQL errors: {graphql_data['errors']}")
                    # Check for common permission errors
                    for error in graphql_data.get('errors', []):
                        if 'read:user' in str(error.get('message', '')):
                            logger.error("GitHub token needs 'read:user' scope for public contributions or 'repo' scope for private contributions")
                    
                if 'data' in graphql_data and graphql_data.get('data', {}).get('user'):
                    try:
                        user_data = graphql_data['data']['user']
                        contribution_collection = user_data.get('contributionsCollection', {})
                        calendar = contribution_collection.get('contributionCalendar', {})
                        weeks = calendar.get('weeks', [])
                        today_count = 0
                        
                        for week in weeks:
                            for day in week.get('contributionDays', []):
                                date = day.get('date')
                                count = day.get('contributionCount', 0)
                                if date:
                                    contribution_map[date] = count
                                    if date == today:
                                        today_count = count
                                        
                        logger.info(f"Got {len(contribution_map)} days of contribution data")
                        logger.info(f"Total contributions: {calendar.get('totalContributions', 0)}")
                        data['contributions_today'] = today_count
                        data['contributions_map'] = contribution_map
                    except Exception as e:
                        logger.error(f"Error parsing GraphQL response: {e}")
                        data['contributions_today'] = 0
                        data['contributions_map'] = {}
                else:
                    logger.warning("No user data in GraphQL response")
                    data['contributions_today'] = 0
                    data['contributions_map'] = {}
            else:
                # GraphQL is required for contribution data
                logger.error(f"GraphQL failed with status {graphql_resp.status_code}")
                logger.error(f"Response: {graphql_resp.text}")
                data['contributions_today'] = 0
                data['contributions_map'] = {}
            
            # Get open PRs
            prs_resp = requests.get(
                f'https://api.github.com/search/issues?q=is:pr+is:open+author:{self.username}',
                headers=headers
            )
            if prs_resp.status_code == 200:
                data['open_prs'] = prs_resp.json()['total_count']
                
            # Get open issues  
            issues_resp = requests.get(
                f'https://api.github.com/search/issues?q=is:issue+is:open+author:{self.username}',
                headers=headers
            )
            if issues_resp.status_code == 200:
                data['open_issues'] = issues_resp.json()['total_count']
                
            # Get notifications count
            notifs_resp = requests.get(
                'https://api.github.com/notifications',
                headers=headers
            )
            if notifs_resp.status_code == 200:
                data['notifications'] = len(notifs_resp.json())
                
            # Get recent commits from events
            commits = []
            seen_messages = set()  # Track unique commits
            
            for event in events[:20]:  # Look through recent events
                if event['type'] == 'PushEvent':
                    repo_name = event['repo']['name'].split('/')[-1]
                    
                    for commit in event['payload'].get('commits', []):
                        message = commit['message'].split('\n')[0][:40]
                        
                        # Skip if we've seen this commit message before
                        if message not in seen_messages:
                            seen_messages.add(message)
                            commits.append({
                                'message': message,
                                'repo': repo_name
                            })
                            
                        if len(commits) >= 2:
                            break
                            
                if len(commits) >= 2:
                    break
                    
            data['recent_commits'] = commits
            
            # No need to set status since we're not showing it
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching GitHub data: {e}")
            return {
                'status': 'Error',
                'status_type': 'error',
                'contributions_today': 0,
                'contributions_map': {},
                'open_prs': 0,
                'open_issues': 0,
                'notifications': 0,
                'recent_commits': []
            }
            
    def update_display(self, data: Dict[str, Any]):
        """Update the display with GitHub data"""
        # Update contributions
        contributions = data.get('contributions_today', 0)
        self.contributions_label.setText(f"Today: {contributions} commits")
        
        # Update heatmap
        self.heatmap.set_data(data.get('contributions_map', {}))
        
        # Update stats
        self.prs_label.setText(f"PRs: {data.get('open_prs', 0)}")
        self.issues_label.setText(f"Issues: {data.get('open_issues', 0)}")
        self.notifs_label.setText(f"Notifs: {data.get('notifications', 0)}")
        
        # Update recent commits
        commits = data.get('recent_commits', [])
        if len(commits) > 0:
            self.commit1_label.setText(f"• {commits[0]['repo']}: {commits[0]['message']}")
        else:
            self.commit1_label.setText("• No recent commits")
            
        if len(commits) > 1:
            self.commit2_label.setText(f"• {commits[1]['repo']}: {commits[1]['message']}")
        else:
            self.commit2_label.setText("")
            
        # Update status
        self.update_status(data.get('status', 'Active'), data.get('status_type', 'normal'))
        
    def scale_content_fonts(self, scale: float):
        """Scale the content fonts"""
        # Scale contributions (1pt smaller than title)
        font = QFont()
        font.setPointSize(int((self.base_font_sizes['title'] - 1) * scale))
        font.setBold(True)
        self.contributions_label.setFont(font)
        
        # Scale stats
        size = int(self.base_font_sizes['small'] * scale)
        self.prs_label.setStyleSheet(f" font-size: {size}px;")
        self.issues_label.setStyleSheet(f" font-size: {size}px;")
        self.notifs_label.setStyleSheet(f" font-size: {size}px;")
        self.recent_label.setStyleSheet(f" font-size: {size}px; margin-top: 5px;")
        
        # Scale commits
        size = int((self.base_font_sizes['small'] - 1) * scale)
        self.commit1_label.setStyleSheet(f" font-size: {size}px;")
        self.commit2_label.setStyleSheet(f" font-size: {size}px;")