import os
import re
import subprocess
from datetime import datetime
from collections import defaultdict, Counter

# 저장 경로 설정
output_directory = r"./"

# 스크립트 설정
specified_author_name = ""
repository_path = r"C:/Users/Git/Project"
git_log_filter = ""
# git_log_filter = "fix*"
git_log_options = ["--no-merges", "--reverse"]
commit_message_replacements = []
# commit_message_replacements = [["^(.+):\s", "["]]

def get_git_remote_url(repository_path):
    """Git 저장소의 원격 URL을 추출합니다."""
    try:
        output = subprocess.check_output(["git", "-C", repository_path, "remote", "get-url", "origin"], text=True)
        remote_url = output.strip().rstrip('.git')
        return remote_url
    except subprocess.CalledProcessError:
        return ""
    
def generate_git_log_command(repository_path, author_name, log_filter, additional_options):
    """Git 로그 명령어를 생성합니다."""
    message_format = "%s"
    remote_url = get_git_remote_url(repository_path)
    if remote_url:
        message_format = f"[%s]({remote_url}/commit/%H)"
    base_command = ["git", "log", f"--pretty=format:%ad - {message_format} @%an", "--date=local", "-i"]
    if author_name:
        base_command[2] = f"--pretty=format:%ad - {message_format}"
        base_command.append(f"--author={author_name}")
    if log_filter:
        base_command.append(f"--grep={log_filter}")
    base_command.extend(additional_options)
    return base_command

def save_git_log_to_file(repository_path, file_path, command):
    """커밋 로그를 파일에 저장합니다."""
    with open(file_path, "w", encoding="utf-8") as file:
        subprocess.run(command, stdout=file, cwd=repository_path, check=True)

def parse_commit_log(commit_log, specified_author):
    """커밋 로그를 분석합니다."""
    log_entries = commit_log.strip().split("\n")
    daily_log_dict, author_commit_counts, hourly_commit_counts, monthly_commit_counts, yearly_commit_counts = defaultdict(list), Counter(), Counter(), Counter(), Counter()
    message_length_total, commit_count = 0, 0

    for entry in log_entries:
        log_match = re.match(r"(\w+ \w+ \d+ \d+:\d+:\d+ \d+) - (.+)", entry)
        if log_match:
            date_string, log_content = log_match.groups()
            log_date = datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
            daily_log_dict[log_date.date()].append(log_content)
            message_length_total += len(log_content)
            
            hourly_commit_counts[log_date.hour] += 1
            monthly_commit_counts[log_date.month] += 1
            yearly_commit_counts[log_date.year] += 1
            
            if specified_author:
                author_commit_counts[specified_author] += 1
            else:
                author_extraction_match = re.match(r"(.+) @(.+)$", log_content)
                if author_extraction_match:
                    message, author = author_extraction_match.groups()
                    author_commit_counts[author] += 1

    commit_count = sum(author_commit_counts.values())
    average_message_length = message_length_total / commit_count if commit_count else 0
    peak_commit_hour = hourly_commit_counts.most_common(1)[0][0] if hourly_commit_counts else None

    return daily_log_dict, author_commit_counts, hourly_commit_counts, monthly_commit_counts, yearly_commit_counts, commit_count, average_message_length, peak_commit_hour

def create_commit_analysis_report(log_dictionary, author_commit_distribution, hourly_commit_distribution, monthly_commit_distribution, yearly_commit_distribution, total_commit_count, mean_message_length, most_active_hour, author_name, project_name):
    """커밋 분석 결과를 포맷팅하여 보고서 형태로 생성합니다."""
    author_report_title = f"@{specified_author_name} " if specified_author_name else ""
    analysis_report = f"# 깃 커밋 로그 분석 보고서 {author_report_title}\n\n"
    analysis_report += f"**분석 프로젝트**: {project_name}\n\n"
    analysis_report += f"**분석 보고서 작성 시각**: {current_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if git_log_filter:
        analysis_report += f"**검색 필터**: {git_log_filter}\n\n"
    
    analysis_report += f"**총 커밋 수**: {total_commit_count}개\n\n"
    analysis_report += f"**평균 커밋 메시지 길이**: {mean_message_length:.2f} 글자\n\n"

    most_commit_day, most_commit_volume = max(log_dictionary.items(), key=lambda x: len(x[1]), default=(None, 0))
    if most_commit_day:
        analysis_report += f"**가장 활발한 커밋 날짜**: {most_commit_day.strftime('%Y년 %m월 %d일')} ({len(most_commit_volume)}개)\n\n"

    if not author_name:
        analysis_report += "**개별 사용자별 커밋 수**:\n"
        for author, count in sorted(author_commit_distribution.items(), key=lambda item: item[1], reverse=True):
            analysis_report += f"  - {author}: {count}개\n"
        analysis_report += "\n"

    if most_active_hour is not None:
        analysis_report += f"**가장 활발한 커밋 시간대**: {most_active_hour}시\n\n"
    if total_commit_count > 0:
        analysis_report += "**시간별 커밋 비율**:\n"
        for hour, count in sorted(hourly_commit_distribution.items(), key=lambda item: (item[1] / total_commit_count), reverse=True):
            commit_percentage = (count / total_commit_count) * 100
            analysis_report += f"  - {str(hour).rjust(2)}시: {commit_percentage:.2f}% ({count}개)\n"
        analysis_report += "\n"

    # 요일별 커밋 분석 추가
    analysis_report += "**요일별 커밋 분석**:\n"
    weekday_names_korean = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    commit_counts_per_day = {day: 0 for day in weekday_names_korean}
    for date in log_dictionary.keys():
        day_of_week_korean = weekday_names_korean[date.weekday()]
        commit_counts_per_day[day_of_week_korean] += len(log_dictionary[date])
    for day in weekday_names_korean:
        analysis_report += f"  - {day}: {commit_counts_per_day[day]}개\n"
    analysis_report += "\n"
        
    # 월별 커밋 분석 추가
    analysis_report += "**월별 커밋 분석**:\n"
    for month, count in sorted(monthly_commit_distribution.items()):
        analysis_report += f"  - {str(month).rjust(2)}월: {count}개\n"
    analysis_report += "\n"

    # 년별 커밋 분석 추가
    analysis_report += "**년별 커밋 분석**:\n"
    for year, count in sorted(yearly_commit_distribution.items()):
        analysis_report += f"  - {year}년: {count}개\n"

    return analysis_report

def format_git_commit_logs(log_dictionary, commit_message_replacements):
    """깃 커밋 로그를 포맷팅합니다."""
    formatted_git_logs = "# 깃 커밋 로그\n\n"
    for date, logs in log_dictionary.items():
        formatted_git_logs += f"##### {date.strftime('%Y년 %m월 %d일')}\n"
        for i, log in enumerate(logs, start=1):
            formatted_log_content = log.strip()
            for pattern, replacement in commit_message_replacements:
                formatted_log_content = re.sub(pattern, replacement, formatted_log_content)
            formatted_git_logs += f"{str(i).rjust(2)}. {formatted_log_content}\n"
        formatted_git_logs += "\n"
    return formatted_git_logs.strip()

def get_git_project_name(repository_path):
    """Git 저장소의 프로젝트 이름을 추출합니다."""
    try:
        output = subprocess.check_output(["git", "-C", repository_path, "remote", "get-url", "origin"], text=True)
        project_name = output.strip().split('/')[-1].rstrip('.git')
        return project_name
    except subprocess.CalledProcessError:
        return "Unknown Project"
    
# 프로젝트 이름 설정
project_name = get_git_project_name(repository_path)

# 파일 저장 경로 및 이름 설정
current_date = datetime.now()
current_date_str = current_date.strftime('%Y-%m-%d')
output_filename = f"{project_name}@{specified_author_name}-{current_date_str}" if specified_author_name else f"{project_name}@All-{current_date_str}"
output_file_path = os.path.join(output_directory, f"{output_filename}.md")

# 깃 로그 파일 저장
git_log_command = generate_git_log_command(repository_path, specified_author_name, git_log_filter, git_log_options)
save_git_log_to_file(repository_path, output_file_path, git_log_command)

# 깃 로그 분석
with open(output_file_path, "r", encoding="utf-8") as file:
    git_commit_log = file.read()

commit_log_dict, commit_counts_by_author, commit_counts_by_hour, commit_counts_by_month, commit_counts_by_year, commit_total, average_commit_message_length, hour_with_most_commits = parse_commit_log(git_commit_log, specified_author_name)

# 분석 결과 보고서 작성 및 저장
commit_analysis_report = create_commit_analysis_report(commit_log_dict, commit_counts_by_author, commit_counts_by_hour, commit_counts_by_month, commit_counts_by_year, commit_total, average_commit_message_length, hour_with_most_commits, specified_author_name, project_name)
formatted_commit_logs = format_git_commit_logs(commit_log_dict, commit_message_replacements)
final_report = f"{commit_analysis_report}\n---\n\n{formatted_commit_logs}"

with open(output_file_path, "w", encoding="utf-8") as file:
    file.write(final_report)

print(f"분석 결과가 '{output_file_path}' 경로에 저장되었습니다.")
