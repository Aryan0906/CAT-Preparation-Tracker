import streamlit as st
import time
from datetime import datetime, timedelta
import sqlite3
from utils import save_study_session, save_timer_session

def init_db():
    """Initialize database connection"""
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()
    
    # Ensure productivity_settings table exists
    c.execute('''CREATE TABLE IF NOT EXISTS productivity_settings
                 (user_id TEXT, focus_duration INTEGER DEFAULT 25, break_duration INTEGER DEFAULT 5,
                  reminder_frequency TEXT, notification_enabled BOOLEAN DEFAULT 1,
                  daily_goal INTEGER DEFAULT 120, reminder_time TEXT DEFAULT '09:00')''')
    
    # Ensure timer_logs table exists
    c.execute('''CREATE TABLE IF NOT EXISTS timer_logs
                 (date TEXT, start_time TEXT, end_time TEXT, duration INTEGER,
                  completed BOOLEAN, topic TEXT)''')
    
    # Ensure study_log table exists
    c.execute('''CREATE TABLE IF NOT EXISTS study_log
                 (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
    
    conn.commit()
    return conn

def show_focus_timer():
    """Display a focus timer with continuous countdown and notifications"""
    st.title("Focus Timer")
    
    # Initialize database connection
    conn = init_db()
    c = conn.cursor()
    
    # Get user settings
    c.execute("SELECT * FROM productivity_settings WHERE user_id = 'default'")
    settings = c.fetchone()
    
    if settings:
        focus_duration = settings[1]  # focus_duration
        break_duration = settings[2]  # break_duration
        notification_enabled = settings[4]  # notification_enabled
    else:
        # Default settings
        focus_duration = 25
        break_duration = 5
        notification_enabled = True
        
        # Insert default settings
        c.execute("""
            INSERT INTO productivity_settings
            (user_id, focus_duration, break_duration, reminder_frequency, notification_enabled, daily_goal, reminder_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("default", focus_duration, break_duration, "daily", notification_enabled, 120, "09:00"))
        conn.commit()
    
    # Create two columns for timer and settings
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Pomodoro Timer")
        
        # Timer settings
        timer_options = {
            "Focus": focus_duration,
            "Short Break": break_duration,
            "Long Break": break_duration * 3
        }
        
        # Timer type selector
        timer_type = st.radio("Timer Type", list(timer_options.keys()))
        selected_duration = timer_options[timer_type]
        
        # Topic selector for focus sessions
        if timer_type == "Focus":
            topic = st.selectbox(
                "What are you working on?",
                ["VARC", "DILR", "Quant", "General Preparation", "Mock Test", "Other"]
            )
            subtopic = st.text_input("Subtopic (optional)")
        else:
            topic = ""
            subtopic = ""
        
        # Initialize timer state in session state
        if 'timer_running' not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.start_time = None
            st.session_state.end_time = None
            st.session_state.remaining_seconds = selected_duration * 60
            st.session_state.timer_type = timer_type
            st.session_state.selected_duration = selected_duration
            st.session_state.topic = topic
            st.session_state.subtopic = subtopic
            st.session_state.timer_completed = False
        
        # Update timer type and duration if changed
        if st.session_state.timer_type != timer_type or st.session_state.selected_duration != selected_duration:
            if not st.session_state.timer_running:
                st.session_state.timer_type = timer_type
                st.session_state.selected_duration = selected_duration
                st.session_state.remaining_seconds = selected_duration * 60
                st.session_state.topic = topic if timer_type == "Focus" else ""
                st.session_state.subtopic = subtopic if timer_type == "Focus" else ""
        
        # Timer controls
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Start" if not st.session_state.timer_running else "Pause"):
                if not st.session_state.timer_running:
                    st.session_state.timer_running = True
                    st.session_state.start_time = datetime.now()
                    st.session_state.end_time = st.session_state.start_time + timedelta(seconds=st.session_state.remaining_seconds)
                else:
                    st.session_state.timer_running = False
                    elapsed = (datetime.now() - st.session_state.start_time).total_seconds()
                    st.session_state.remaining_seconds = max(0, st.session_state.remaining_seconds - elapsed)
                    st.session_state.start_time = None
                st.rerun()
        
        with col2:
            if st.button("Reset"):
                st.session_state.timer_running = False
                st.session_state.start_time = None
                st.session_state.end_time = None
                st.session_state.remaining_seconds = selected_duration * 60
                st.session_state.timer_completed = False
                st.rerun()
        
        with col3:
            if timer_type == "Focus" and st.button("Complete"):
                if st.session_state.start_time or st.session_state.timer_running:
                    # Calculate time spent
                    if st.session_state.timer_running:
                        elapsed = (datetime.now() - st.session_state.start_time).total_seconds()
                        minutes_spent = int((selected_duration * 60 - st.session_state.remaining_seconds + elapsed) / 60)
                    else:
                        minutes_spent = int((selected_duration * 60 - st.session_state.remaining_seconds) / 60)
                    
                    # Save to database
                    if minutes_spent > 0:
                        try:
                            save_study_session(topic, subtopic, minutes_spent)
                            save_timer_session(
                                st.session_state.start_time or datetime.now() - timedelta(minutes=minutes_spent),
                                datetime.now(),
                                minutes_spent * 60,
                                True,
                                topic
                            )
                            st.success(f"Saved {minutes_spent} minutes of study on {topic}")
                        except Exception as e:
                            st.error(f"Error saving session: {str(e)}")
                    
                    # Reset timer
                    st.session_state.timer_running = False
                    st.session_state.start_time = None
                    st.session_state.end_time = None
                    st.session_state.remaining_seconds = selected_duration * 60
                    st.session_state.timer_completed = False
                    st.rerun()
        
        # JavaScript for continuous timer
        if st.session_state.timer_running:
            current_time = datetime.now()
            if st.session_state.end_time:
                remaining = max(0, (st.session_state.end_time - current_time).total_seconds())
                
                # Check if timer is complete
                if remaining <= 0 and not st.session_state.timer_completed:
                    st.session_state.timer_completed = True
                    st.session_state.timer_running = False
                    
                    # Save completed timer session to database
                    if st.session_state.timer_type == "Focus":
                        try:
                            save_timer_session(
                                st.session_state.start_time,
                                datetime.now(),
                                selected_duration * 60,
                                True,
                                topic
                            )
                            save_study_session(topic, subtopic, selected_duration)
                            st.success(f"Saved {selected_duration} minutes of study on {topic}")
                        except Exception as e:
                            st.error(f"Error saving timer session: {str(e)}")
                        st.rerun()
            else:
                remaining = st.session_state.remaining_seconds
        else:
            remaining = st.session_state.remaining_seconds
        
        # Format time as mm:ss
        mins, secs = divmod(int(remaining), 60)
        timer_display = f"{mins:02d}:{secs:02d}"
        
        # JavaScript for continuous timer and notification
        js_code = f"""
        <script>
            (function() {{
                // Store timer state
                const timerState = {{
                    endTime: {int(st.session_state.end_time.timestamp() * 1000) if st.session_state.timer_running and st.session_state.end_time else int((datetime.now() + timedelta(hours=24)).timestamp() * 1000)},
                    isRunning: {str(st.session_state.timer_running).lower()},
                    timerType: "{st.session_state.timer_type}",
                    notified: false,
                    intervalId: null
                }};
                
                // Request notification permission
                if ("Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {{
                    Notification.requestPermission();
                }}
                
                // Function to update timer display
                function updateTimerDisplay() {{
                    if (!timerState.isRunning) return;
                    
                    const now = new Date().getTime();
                    const timeLeft = Math.max(0, timerState.endTime - now);
                    
                    // Calculate minutes and seconds
                    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
                    
                    // Format display
                    const displayMinutes = String(minutes).padStart(2, '0');
                    const displaySeconds = String(seconds).padStart(2, '0');
                    
                    // Update the timer display
                    const timerElement = document.getElementById('timer-display');
                    if (timerElement) {{
                        timerElement.innerText = displayMinutes + ':' + displaySeconds;
                    }}
                    
                    // Update progress bar
                    const progressBar = document.querySelector('.stProgress > div');
                    if (progressBar) {{
                        const progress = 1 - (timeLeft / ({selected_duration * 60 * 1000}));
                        progressBar.style.width = Math.min(100, Math.max(0, progress * 100)) + '%';
                    }}
                    
                    // Check if timer is complete
                    if (timeLeft <= 0 && !timerState.notified) {{
                        timerState.notified = true;
                        timerState.isRunning = false;
                        
                        // Play sound
                        try {{
                            const audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-alarm-digital-clock-beep-989.mp3');
                            audio.play();
                        }} catch(e) {{
                            console.error('Error playing sound:', e);
                        }}
                        
                        // Show notification
                        try {{
                            if ("Notification" in window && Notification.permission === "granted") {{
                                const notification = new Notification("Timer Complete!", {{
                                    body: timerState.timerType + " session is complete!",
                                    icon: "https://cdn-icons-png.flaticon.com/512/3652/3652191.png"
                                }});
                            }}
                        }} catch(e) {{
                            console.error('Error showing notification:', e);
                        }}
                        
                        // Show alert
                        setTimeout(() => {{
                            alert(timerState.timerType + " session is complete!");
                            // Reload the page to update Streamlit state
                            window.location.reload();
                        }}, 100);
                    }}
                }}
                
                // Start timer interval
                if (timerState.isRunning) {{
                    timerState.intervalId = setInterval(updateTimerDisplay, 100);
                }}
                
                // Handle page visibility changes
                document.addEventListener('visibilitychange', function() {{
                    if (document.visibilityState === 'visible' && timerState.isRunning) {{
                        updateTimerDisplay();
                    }}
                }});
                
                // Prevent accidental navigation
                window.addEventListener('beforeunload', function(e) {{
                    if (timerState.isRunning) {{
                        e.preventDefault();
                        e.returnValue = 'Timer is still running. Are you sure you want to leave?';
                        return 'Timer is still running. Are you sure you want to leave?';
                    }}
                }});
            }})();
        </script>
        """
        
        # Display large timer with ID for JavaScript to update
        st.markdown(f"<h1 id='timer-display' style='text-align: center; font-size: 6em;'>{timer_display}</h1>", unsafe_allow_html=True)
        
        # Add JavaScript to page
        st.markdown(js_code, unsafe_allow_html=True)
        
        # Progress bar
        progress = 1 - (remaining / (selected_duration * 60))
        st.progress(min(1.0, max(0.0, progress)))
        
        # Display message based on timer type
        if timer_type == "Focus":
            st.info(f"Focus on your {topic} studies. Stay concentrated!")
        elif timer_type == "Short Break":
            st.success("Take a short break. Stretch, hydrate, and relax your eyes.")
        else:  # Long Break
            st.success("Take a longer break. Get up, move around, and refresh your mind.")
        
        # Notification settings
        st.checkbox("Enable notifications when timer completes", value=notification_enabled, key="notification_toggle")
        if st.session_state.get("notification_toggle") != notification_enabled:
            # Update notification setting in database
            c.execute("""
                UPDATE productivity_settings
                SET notification_enabled = ?
                WHERE user_id = ?
            """, (st.session_state.notification_toggle, "default"))
            conn.commit()
    
    with col2:
        st.header("Timer Settings")
        
        # Form for updating timer settings
        with st.form("timer_settings"):
            new_focus = st.number_input("Focus Duration (minutes)", min_value=1, max_value=60, value=focus_duration)
            new_break = st.number_input("Break Duration (minutes)", min_value=1, max_value=30, value=break_duration)
            
            submitted = st.form_submit_button("Update Settings")
            if submitted:
                # Update settings in database
                c.execute("""
                    UPDATE productivity_settings
                    SET focus_duration = ?, break_duration = ?
                    WHERE user_id = ?
                """, (new_focus, new_break, "default"))
                conn.commit()
                st.success("Settings updated!")
                st.rerun()
        
        # Display study session history
        st.subheader("Recent Study Sessions")
        
        # Get recent study sessions
        c.execute("""
            SELECT date, topic, time_spent
            FROM study_log
            ORDER BY date DESC, rowid DESC
            LIMIT 5
        """)
        sessions = c.fetchall()
        
        if sessions:
            for date, topic, time_spent in sessions:
                st.write(f"{date} - {topic}: {time_spent} minutes")
        else:
            st.info("No study sessions recorded yet.")
        
        # Display daily goal progress
        st.subheader("Daily Goal Progress")
        
        # Get today's study time
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("""
            SELECT SUM(time_spent)
            FROM study_log
            WHERE date = ?
        """, (today,))
        today_minutes = c.fetchone()[0] or 0
        
        # Get daily goal from settings
        c.execute("SELECT daily_goal FROM productivity_settings WHERE user_id = 'default'")
        daily_goal = c.fetchone()
        if daily_goal:
            daily_goal = daily_goal[0]
        else:
            daily_goal = 120  # Default 2 hours
        
        # Display progress
        progress = min(1.0, today_minutes / daily_goal)
        st.progress(progress)
        st.write(f"{today_minutes} / {daily_goal} minutes ({int(progress * 100)}%)")
    
    # Close database connection
    conn.close()
