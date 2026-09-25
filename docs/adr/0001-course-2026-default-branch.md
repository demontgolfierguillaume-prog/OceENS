# Make `course-2026` the default branch during the semester

For the 2026–27 *Complex Web Services* course, around twenty students fork OcéENS from the repository's default branch. Therefore, `course-2026` is the default branch for the course: student forks are based on it, and course pull requests target it (including development login #82 and role-based seed data #84).

The `main` branch remains untouched during the semester. This gives students a stable course baseline and avoids mixing course-specific code into the upstream default branch. No synchronization from `main` to `course-2026` is planned before the end of the semester.
