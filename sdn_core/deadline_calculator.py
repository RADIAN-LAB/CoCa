"""
Dynamic deadline calculation for VANET tasks based on task type and priority.

Task types represent different application categories:
- Type 0-2: Safety-critical (emergency braking, collision warnings)
- Type 3-5: Traffic management (route planning, traffic updates)
- Type 6-9: Infotainment (video streaming, map updates)

Higher priority (5) = more urgent = shorter deadline
Lower priority (1) = less urgent = longer deadline
"""

def calculate_dynamic_deadline(task_type: int, priority: int) -> float:
    """
    Calculate dynamic deadline based on task type and priority.
    
    Args:
        task_type: Task type (0-9)
        priority: Priority level (1-5, where 5 is most urgent)
        
    Returns:
        Deadline in seconds (range: 3-20 seconds)
    """
    # Base deadlines for each task category (in seconds)
    if task_type <= 2:
        # Safety-critical: shortest base deadline
        base_deadline = 15.0
    elif task_type <= 5:
        # Traffic management: medium base deadline
        base_deadline = 25.0
    else:
        # Infotainment: longest base deadline
        base_deadline = 40.0
    
    # Calculate deadline: higher priority = shorter deadline
    # Priority 5 (urgent) gets base/5, Priority 1 (low) gets base/1
    deadline = base_deadline / priority
    
    # Cap maximum deadline at 20 seconds
    deadline = min(deadline, 20.0)
    
    # Ensure minimum deadline of 3 seconds
    deadline = max(deadline, 3.0)
    
    return deadline


def get_deadline_statistics(tasks_data):
    """
    Calculate statistics about deadlines for a set of tasks.
    
    Args:
        tasks_data: List of task dictionaries with 'task_type' and 'priority'
        
    Returns:
        Dictionary with deadline statistics
    """
    deadlines = [calculate_dynamic_deadline(t['task_type'], t['priority']) 
                 for t in tasks_data]
    
    return {
        'min': min(deadlines),
        'max': max(deadlines),
        'mean': sum(deadlines) / len(deadlines),
        'median': sorted(deadlines)[len(deadlines) // 2]
    }


# Example deadline table for reference
DEADLINE_EXAMPLES = {
    'Safety-Critical (Type 0-2)': {
        'Priority 5 (Urgent)': 3.0,
        'Priority 4 (High)': 3.75,
        'Priority 3 (Medium)': 5.0,
        'Priority 2 (Normal)': 7.5,
        'Priority 1 (Low)': 15.0,
    },
    'Traffic Management (Type 3-5)': {
        'Priority 5 (Urgent)': 5.0,
        'Priority 4 (High)': 6.25,
        'Priority 3 (Medium)': 8.33,
        'Priority 2 (Normal)': 12.5,
        'Priority 1 (Low)': 20.0,
    },
    'Infotainment (Type 6-9)': {
        'Priority 5 (Urgent)': 8.0,
        'Priority 4 (High)': 10.0,
        'Priority 3 (Medium)': 13.33,
        'Priority 2 (Normal)': 20.0,
        'Priority 1 (Low)': 20.0,
    }
}
