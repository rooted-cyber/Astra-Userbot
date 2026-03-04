def get_progress_bar(percentage: float, size: int = 15) -> str:
    """
    Generates a progress bar string
    :param percentage: Progress percentage (0 to 100)
    :param size: Number of blocks in the bar
    :return: Formatted progress bar: [■■■□□□] 50%
    """
    percentage = max(0, min(100, percentage))
    filled_size = int((percentage / 100) * size)
    empty_size = size - filled_size

    # Using characters that work well on WhatsApp
    filled = "●" * filled_size
    empty = "○" * empty_size

    return f"[{filled}{empty}] {percentage:.1f}%"
