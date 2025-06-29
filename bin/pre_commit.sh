#!/bin/bash

BASE_PATH="$(dirname "$0")"
source "$BASE_PATH/colors.sh"
EXIT_CODE=0


################################################################################
#                                   ISORT                                      #
################################################################################
echo -n "${Cyan}Formatting import with isort... $Color_Off"
out=$(isort dwh_fhir/ apps/)
if [ ! -z "$out" ] ; then
  echo ""
  echo -e "$out"
fi
echo "${Green}Ok ✅ $Color_Off"
echo ""


################################################################################
#                                   BLACK                                      #
################################################################################
echo "${Cyan}Formatting code with black...$Color_Off"
black -l 120 dwh_fhir/ apps/
echo ""


################################################################################
#                                  FLAKE 8                                     #
################################################################################
echo -n "${Cyan}Running flake8... $Color_Off"
out=$(flake8 .)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################
#                                PYDOCSTYLE                                    #
################################################################################
echo -n "${Cyan}Running pydocstyle... $Color_Off"
out=$(pydocstyle --count dwh_fhir/ apps/)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################
#                                   MYPY                                       #
################################################################################
echo -n "${Cyan}Running mypy... $Color_Off"
out=$(mypy dwh_fhir/ apps/ --disallow-untyped-def)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################
#                                  BANDIT                                      #
################################################################################
echo -n "${Cyan}Running bandit... $Color_Off"
out=$(bandit --ini=setup.cfg -ll 2> /dev/null)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################
#                                  SWAGGER                                     #
################################################################################
echo -n "${Cyan}Checking for swagger errors / warnings.. $Color_Off"
out=$(python3 manage.py spectacular --fail-on-warn &> /dev/null)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Errors or warning found !$Color_Off"
  echo "${Red}Run 'python3 manage.py spectacular --fail-on-warn' to display the errors !$Color_Off"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################
#                                MIGRATIONS                                    #
################################################################################
echo -n "${Cyan}Checking for missing migrations... $Color_Off"
out=$(python3 manage.py makemigrations --check --dry-run --no-input &> /dev/null)
if [ "$?" -ne 0 ] ; then
  echo "${Red}migrations are missing !$Color_Off"
  echo "${Red}Run 'python3 manage.py makemigrations' before committing !$Color_Off"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################


if [ $EXIT_CODE = 1 ] ; then
   echo "${Red}⚠ You must fix the errors before committing ⚠$Color_Off"
   exit $EXIT_CODE
fi
echo "${Purple}✨ You can commit without any worry ✨$Color_Off"
