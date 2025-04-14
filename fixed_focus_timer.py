def show_focus_timer():
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

        # Initialize timer state in session state
        if 'timer_running' not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.start_time = None
            st.session_state.end_time = None
            st.session_state.remaining_time = selected_duration * 60
            st.session_state.elapsed_time = 0
            st.session_state.timer_completed = False
            st.session_state.timer_type = timer_type
            st.session_state.selected_duration = selected_duration
            st.session_state.topic = topic if timer_type == "Focus" else ""
            st.session_state.subtopic = subtopic if timer_type == "Focus" else ""
            st.session_state.last_update_time = datetime.now()

        # Update timer type and duration if changed
        if st.session_state.timer_type != timer_type or st.session_state.selected_duration != selected_duration:
            if not st.session_state.timer_running:
                st.session_state.timer_type = timer_type
                st.session_state.selected_duration = selected_duration
                st.session_state.remaining_time = selected_duration * 60
                st.session_state.elapsed_time = 0
                st.session_state.timer_completed = False
                st.session_state.topic = topic if timer_type == "Focus" else ""
                st.session_state.subtopic = subtopic if timer_type == "Focus" else ""

        # Timer controls
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("Start" if not st.session_state.timer_running else "Pause"):
                if not st.session_state.timer_running:
                    st.session_state.timer_running = True
                    st.session_state.start_time = datetime.now()
                    st.session_state.end_time = st.session_state.start_time + timedelta(seconds=st.session_state.remaining_time)
                    st.session_state.timer_completed = False
                else:
                    st.session_state.timer_running = False
                    st.session_state.elapsed_time += (datetime.now() - st.session_state.start_time).total_seconds()
                    st.session_state.remaining_time = max(0, selected_duration * 60 - st.session_state.elapsed_time)
                st.rerun()

        with col2:
            if st.button("Reset"):
                st.session_state.timer_running = False
                st.session_state.start_time = None
                st.session_state.end_time = None
                st.session_state.remaining_time = selected_duration * 60
                st.session_state.elapsed_time = 0
                st.session_state.timer_completed = False
                st.rerun()

        with col3:
            if timer_type == "Focus" and st.button("Complete"):
                if 'start_time' in st.session_state and st.session_state.start_time:
                    # Calculate time spent
                    if st.session_state.timer_running:
                        elapsed = st.session_state.elapsed_time + (datetime.now() - st.session_state.start_time).total_seconds()
                    else:
                        elapsed = st.session_state.elapsed_time

                    # Convert to minutes
                    minutes_spent = int(elapsed / 60)

                    # Save to database
                    if minutes_spent > 0:
                        try:
                            save_study_session(topic, subtopic, minutes_spent)
                            st.success(f"Saved {minutes_spent} minutes of study on {topic}")
                        except Exception as e:
                            st.error(f"Error saving study session: {str(e)}")

                    # Reset timer
                    st.session_state.timer_running = False
                    st.session_state.start_time = None
                    st.session_state.end_time = None
                    st.session_state.remaining_time = selected_duration * 60
                    st.session_state.elapsed_time = 0
                    st.session_state.timer_completed = False
                    st.rerun()

        # Always include JavaScript for continuous timer
        # Calculate end time in milliseconds since epoch
        if st.session_state.timer_running and st.session_state.end_time:
            end_time_ms = int(st.session_state.end_time.timestamp() * 1000)
            is_running = "true"
        else:
            # Use a future time as placeholder when not running
            end_time_ms = int((datetime.now() + timedelta(hours=24)).timestamp() * 1000)
            is_running = "false"

        total_duration_secs = selected_duration * 60
        timer_type = st.session_state.timer_type if 'timer_type' in st.session_state else timer_type

        # JavaScript for continuous timer and notification
        js_code = f"""
        <script>
            (function() {{
                // Store timer state in window object so it persists across Streamlit reruns
                if (!window.timerState) {{
                    window.timerState = {{
                        endTime: {end_time_ms},
                        isRunning: {is_running},
                        totalDuration: {total_duration_secs},
                        timerType: "{timer_type}",
                        notified: false,
                        intervalId: null,
                        lastUpdateTime: new Date().getTime()
                    }};
                }} else {{
                    // Always update these values to ensure they're current
                    window.timerState.endTime = {end_time_ms};
                    window.timerState.isRunning = {is_running};
                    window.timerState.totalDuration = {total_duration_secs};
                    window.timerState.timerType = "{timer_type}";

                    // Only reset notification state when starting a new timer
                    if ({is_running} === true && !window.timerState.isRunning) {{
                        window.timerState.notified = false;
                        console.log("Timer started: " + new Date());
                    }}
                }}
                
                // Make sure we have permission for notifications
                if ("Notification" in window) {{
                    if (Notification.permission !== "granted" && Notification.permission !== "denied") {{
                        Notification.requestPermission();
                    }}
                }}

                // Function to update the timer display
                function updateTimerDisplay() {{
                    // Always update the display, even if not running (to show correct time)
                    const now = new Date().getTime();
                    const timeLeft = Math.max(0, window.timerState.endTime - now);

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
                    const progress = 1 - (timeLeft / 1000 / window.timerState.totalDuration);
                    const progressBar = document.querySelector('.stProgress > div');
                    if (progressBar) {{
                        progressBar.style.width = Math.min(100, Math.max(0, progress * 100)) + '%';
                    }}

                    // Check if timer is complete
                    if (window.timerState.isRunning && timeLeft <= 0 && !window.timerState.notified) {{
                        window.timerState.notified = true;
                        window.timerState.isRunning = false;

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
                                    body: window.timerState.timerType + " session is complete!",
                                    icon: "https://cdn-icons-png.flaticon.com/512/3652/3652191.png"
                                }});
                            }}
                        }} catch(e) {{
                            console.error('Error showing notification:', e);
                        }}

                        // Show alert
                        setTimeout(() => {{
                            alert(window.timerState.timerType + " session is complete!");
                        }}, 100);

                        // Communicate completion to Streamlit
                        try {{
                            // Find the hidden input field and set its value
                            const inputs = Array.from(window.parent.document.querySelectorAll('input[type="text"]'));
                            const hiddenInput = inputs.find(input => !input.value && input.parentElement.style.display !== 'none');
                            if (hiddenInput) {{
                                hiddenInput.value = "completed";
                                hiddenInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                console.log("Timer completion signal sent to Streamlit");
                            }}
                        }} catch(e) {{
                            console.error('Error communicating with Streamlit:', e);
                        }}

                        // Stop the timer
                        window.timerState.isRunning = false;
                    }}

                    // Update last update time
                    window.timerState.lastUpdateTime = now;
                }}

                // Function to start the timer interval
                function startTimerInterval() {{
                    // Clear any existing interval first
                    if (window.timerState.intervalId) {{
                        clearInterval(window.timerState.intervalId);
                        window.timerState.intervalId = null;
                    }}

                    // Create a new interval that runs every 100ms for smoother updates
                    updateTimerDisplay(); // Update immediately
                    window.timerState.intervalId = setInterval(updateTimerDisplay, 100);

                    // Log that timer started
                    console.log("Timer interval started", new Date());
                }}

                // Always start the interval to keep the display updated
                startTimerInterval();

                // Add event listener to handle page visibility changes
                document.addEventListener('visibilitychange', function() {{
                    if (document.visibilityState === 'visible') {{
                        // Page is now visible, restart the interval if it's not running
                        if (!window.timerState.intervalId) {{
                            startTimerInterval();
                        }}
                        // Force an immediate update
                        updateTimerDisplay();
                    }}
                }});

                // Add event listener for beforeunload to prevent accidental navigation away
                window.addEventListener('beforeunload', function(e) {{
                    if (window.timerState.isRunning) {{
                        // Standard way of showing a confirmation dialog
                        e.preventDefault();
                        e.returnValue = 'Timer is still running. Are you sure you want to leave?';
                        return 'Timer is still running. Are you sure you want to leave?';
                    }}
                }});
            }})();
        </script>
        """
        st.markdown(js_code, unsafe_allow_html=True)

        # Add a hidden field to track timer completion from JavaScript
        timer_completed_from_js = st.empty()

        # Check for timer completion from JavaScript
        timer_completed_value = timer_completed_from_js.text_input("", key="timer_completed_signal", label_visibility="collapsed")
        if timer_completed_value == "completed" and st.session_state.timer_running and not st.session_state.timer_completed:
            st.session_state.timer_completed = True
            st.session_state.timer_running = False

            # Save completed timer session to database
            if st.session_state.timer_type == "Focus":
                try:
                    save_timer_session(
                        st.session_state.start_time,
                        st.session_state.end_time or datetime.now(),
                        st.session_state.selected_duration * 60,
                        True,
                        st.session_state.topic
                    )
                    # Also save as study session
                    save_study_session(
                        st.session_state.topic,
                        st.session_state.subtopic,
                        st.session_state.selected_duration
                    )
                    st.success(f"Saved {st.session_state.selected_duration} minutes of study on {st.session_state.topic}")
                except Exception as e:
                    st.error(f"Error saving timer session: {str(e)}")
                st.rerun()

        # Calculate remaining time
        current_time = datetime.now()
        if st.session_state.timer_running and st.session_state.end_time:
            remaining = max(0, (st.session_state.end_time - current_time).total_seconds())
            # Check if timer should be completed based on time
            if remaining <= 0 and not st.session_state.timer_completed:
                st.session_state.timer_completed = True
                st.session_state.timer_running = False

                # Save completed timer session to database
                if st.session_state.timer_type == "Focus":
                    try:
                        save_timer_session(
                            st.session_state.start_time,
                            st.session_state.end_time,
                            st.session_state.selected_duration * 60,
                            True,
                            st.session_state.topic
                        )
                        # Also save as study session
                        save_study_session(
                            st.session_state.topic,
                            st.session_state.subtopic,
                            st.session_state.selected_duration
                        )
                        st.success(f"Saved {st.session_state.selected_duration} minutes of study on {st.session_state.topic}")
                    except Exception as e:
                        st.error(f"Error saving timer session: {str(e)}")
                    st.rerun()
        else:
            remaining = max(0, selected_duration * 60 - st.session_state.elapsed_time)

        # Format time as mm:ss
        mins, secs = divmod(int(remaining), 60)
        timer_display = f"{mins:02d}:{secs:02d}"

        # Display large timer with ID for JavaScript to update
        st.markdown(f"<h1 id='timer-display' style='text-align: center; font-size: 6em;'>{timer_display}</h1>", unsafe_allow_html=True)

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
