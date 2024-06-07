#!/bin/bash
# ----------------------------------------------------------
# [Name]
# Lambdaアップロードするzipファイルの生成
#
# [Arguments]
#  - None
#
# [Return]
#  - 0(成功)
#
# [Since]
# 2024/06/08
# ----------------------------------------------------------

readonly RESULT_SUCCESSED=0
readonly RESULT_FAILED=1

create_zip() {
  local -r _PACKAGE_NAME=package
  local -r _REQUIREMENT_TXT_FILE_NAME=requirements.txt
  local -r _APP_FILE_NAME=line_to_bot.py
  local -r _ZIP_FILE_NAME=line_to_bot.zip
  
  rm -rf ${_PACKAGE_NAME}
  mkdir ${_PACKAGE_NAME}

  pip install -r ${_REQUIREMENT_TXT_FILE_NAME} -t ${_PACKAGE_NAME}/
  
  cp ${_APP_FILE_NAME} ${_PACKAGE_NAME}/
  cp .env ${_PACKAGE_NAME}/

  cd ${_PACKAGE_NAME}
  zip -r ../${_ZIP_FILE_NAME} .
  cd ..

  return ${RESULT_SUCCESSED}
}


main() {
  create_zip
  return ${RESULT_SUCCESSED}
}

main "$@"
exit $?