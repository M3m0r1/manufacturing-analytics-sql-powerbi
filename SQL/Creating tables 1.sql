USE Mfg_Analytics;
GO

-- =========================================================
-- dim_date: календар. 1 рядок = 1 день (183 рядки)
-- =========================================================
CREATE TABLE dim_date (
    date_id      INT          NOT NULL PRIMARY KEY,  -- ключ дня числом: 20260401 = 1 квітня 2026
    [date]       DATE         NOT NULL,              -- сама дата (2026-04-01)
    [year]       INT          NOT NULL,              -- рік (2026)
    [month]      INT          NOT NULL,              -- номер місяця (4 = квітень ... 9 = вересень)
    month_name   VARCHAR(20)  NOT NULL,              -- назва місяця (April)
    [week]       INT          NOT NULL,              -- номер тижня в році (ISO)
    day_of_week  INT          NOT NULL,              -- день тижня: 1 = Пн ... 7 = Нд
    day_name     VARCHAR(20)  NOT NULL,              -- назва дня (Monday)
    is_weekend   BIT          NOT NULL               -- 1 = субота або неділя, 0 = будній день
);

-- =========================================================
-- shifts: зміни. 2 рядки (Day, Night)
-- =========================================================
CREATE TABLE shifts (
    shift_id          INT         NOT NULL PRIMARY KEY, -- ключ зміни: 1 = Day, 2 = Night
    shift_name        VARCHAR(20) NOT NULL,             -- назва зміни
    start_time        VARCHAR(5)  NOT NULL,             -- початок (08:00 або 20:00)
    end_time          VARCHAR(5)  NOT NULL,             -- кінець (20:00 або 08:00)
    crosses_midnight  BIT         NOT NULL,             -- 1 = зміна закінчується наступної доби (Night)
    planned_break_min INT         NOT NULL,             -- планові перерви, хвилин (60)
    planned_run_min   INT         NOT NULL              -- робочі хвилини = 720 - перерви = 660
);

-- =========================================================
-- products: продукти. 4 рядки
-- =========================================================
CREATE TABLE products (
    product_id        INT           NOT NULL PRIMARY KEY, -- ключ продукту (1-4)
    product_code      VARCHAR(20)   NOT NULL,             -- код (MS-100, DS-100, HB-200, FS-300)
    product_name      VARCHAR(100)  NOT NULL,             -- назва (Motion Sensor ...)
    category          VARCHAR(50)   NOT NULL,             -- категорія (Motion & Opening, Control Unit, Fire Detection)
    material_cost_uah DECIMAL(10,2) NOT NULL              -- вартість матеріалів на 1 виріб, грн
);

-- =========================================================
-- production_lines: виробничі лінії. 4 рядки
-- =========================================================
CREATE TABLE production_lines (
    line_id   INT         NOT NULL PRIMARY KEY, -- ключ лінії (1-4)
    line_name VARCHAR(20) NOT NULL,             -- назва (Line A ... Line D)
    line_type VARCHAR(20) NOT NULL              -- тип: Sensors, Hubs, Flexible
);

-- =========================================================
-- production_stages: етапи виробництва. 7 рядків
-- =========================================================
CREATE TABLE production_stages (
    stage_id             INT          NOT NULL PRIMARY KEY, -- ключ етапу (1-7)
    stage_name           VARCHAR(50)  NOT NULL,             -- назва (SMT Assembly ... Packaging)
    stage_order          INT          NOT NULL,             -- порядок проходження (1 = перший)
    cost_accumulated_pct DECIMAL(5,2) NOT NULL              -- яка ЧАСТКА вартості вже вкладена до кінця етапу (0..1)
);

-- =========================================================
-- product_routing: нормативи. 1 рядок = продукт x етап (28 рядків)
-- =========================================================
CREATE TABLE product_routing (
    product_id           INT          NOT NULL,                         -- який продукт
    stage_id             INT          NOT NULL,                         -- який етап
    std_minutes_per_unit DECIMAL(5,2) NOT NULL,                         -- нормативний час на 1 виріб на цьому етапі, хвилин
    PRIMARY KEY (product_id, stage_id),                                 -- пара продукт + етап не повторюється
    FOREIGN KEY (product_id) REFERENCES products(product_id),           -- продукт має існувати
    FOREIGN KEY (stage_id)   REFERENCES production_stages(stage_id)     -- етап має існувати
);

-- =========================================================
-- defect_types: типи дефектів. 8 рядків
-- =========================================================
CREATE TABLE defect_types (
    defect_type_id   INT         NOT NULL PRIMARY KEY, -- ключ дефекту (1-8)
    defect_name      VARCHAR(50) NOT NULL,             -- назва (Solder Bridge, Cold Solder Joint ...)
    typical_stage_id INT         NOT NULL,             -- етап, де цей дефект трапляється найчастіше
    severity         VARCHAR(20) NOT NULL,             -- серйозність: Minor, Major, Critical
    FOREIGN KEY (typical_stage_id) REFERENCES production_stages(stage_id)  -- етап має існувати
);

-- =========================================================
-- downtime_reasons: причини простоїв. 6 рядків
-- =========================================================
CREATE TABLE downtime_reasons (
    reason_id   INT         NOT NULL PRIMARY KEY, -- ключ причини (1-6)
    reason_name VARCHAR(50) NOT NULL,             -- назва (Component Shortage, Machine Breakdown ...)
    category    VARCHAR(30) NOT NULL,             -- група: Material, Technical, Organizational
    is_planned  BIT         NOT NULL              -- 1 = плановий простій, 0 = аварійний
);

-- =========================================================
-- employees: співробітники. 30 рядків
-- =========================================================
CREATE TABLE employees (
    employee_id      INT          NOT NULL PRIMARY KEY,             -- ключ співробітника (1-30)
    full_name        VARCHAR(50)  NOT NULL,                         -- вигадане ім'я (Employee 001)
    role             VARCHAR(20)  NOT NULL,                         -- посада: Operator, Tester, Inspector
    shift_id         INT          NOT NULL,                         -- у якій зміні працює
    line_id          INT          NOT NULL,                         -- на якій лінії працює
    experience_years DECIMAL(4,1) NOT NULL,                         -- досвід, років
    FOREIGN KEY (shift_id) REFERENCES shifts(shift_id),             -- зміна має існувати
    FOREIGN KEY (line_id)  REFERENCES production_lines(line_id)     -- лінія має існувати
);
GO

