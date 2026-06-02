# Runbook

## Run full pipeline

```sql
CALL CONTROL.SP_PROCESS_CHANGED_DATASETS(7, 3);
```

## Run one dataset

```sql
CALL CONTROL.SP_PROCESS_ONE_DATASET('CUSTOMER', 7, 3);
```

## Check run summary

```sql
SELECT *
FROM CONTROL.VW_RUN_SUMMARY
ORDER BY STARTED_AT DESC;
```

## Check failed files

```sql
SELECT *
FROM CONTROL.VW_FAILED_FILES
ORDER BY UPDATED_AT DESC;
```

## Check dataset health

```sql
SELECT *
FROM CONTROL.VW_DATASET_HEALTH
ORDER BY DATASET_NAME;
```

## Reset a failed file for retry

```sql
UPDATE CONTROL.FILE_CONTROL
SET STATUS = 'FAILED_RETRYABLE',
    ERROR_MESSAGE = 'Manually reset for retry',
    UPDATED_AT = CURRENT_TIMESTAMP()
WHERE DATASET_NAME = 'CUSTOMER'
  AND FILE_PATH = '<file path>';
```

## Disable dataset

```sql
UPDATE CONTROL.CFG_DATASET
SET ENABLED = FALSE,
    UPDATED_AT = CURRENT_TIMESTAMP()
WHERE DATASET_NAME = 'CUSTOMER';
```

## Generate AI DQ suggestions

```sql
CALL CONTROL.SP_AI_SUGGEST_DQ_RULES('CUSTOMER', 10);
```
