.DEFAULT_GOAL := help
.PHONY: help grades assignments

help:
	@echo "Available targets:"
	@echo "  grades         - Run 'python3 get-assignments.py --view grades' (optional COURSE_NAME)"
	@echo "  assignments    - Run 'python3 get-assignments.py --view assignments' (optional COURSE_NAME)"
	@echo ""
	@echo "Examples:"
	@echo "  make grades"
	@echo "  make grades COURSE_NAME=your_course"
	@echo "  make assignments"
	@echo "  make assignments COURSE_NAME=your_course"

grades:
	@{ \
	if [ -z "$(COURSE_NAME)" ]; then \
		python3 get-assignments.py --view grades; \
	else \
		python3 get-assignments.py --view grades --course_name=$(COURSE_NAME); \
	fi; \
	}

assignments:
	@{ \
	if [ -z "$(COURSE_NAME)" ]; then \
		python3 get-assignments.py --view assignments; \
	else \
		python3 get-assignments.py --view assignments --course_name=$(COURSE_NAME); \
	fi; \
	}
