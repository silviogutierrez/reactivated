BEGIN;
    DROP TYPE IF EXISTS "samples_opera_tags_enum[]";
                                                                                                                                                                                                                             CREATE TYPE "samples_opera_tags_enum[]" AS ENUM ('MELODIC', 'ROMANTIC', 'LONG');
ALTER TABLE "samples_opera" ALTER COLUMN "tags" SET DATA TYPE samples_opera_tags_enum[] USING tags::samples_opera_tags_enum[];
COMMIT;
