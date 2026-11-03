USE Ajax_Mfg_Analytics;
GO

-- production_plan: план. 1 рядок = день x лінія x продукт
CREATE TABLE production_plan (
    plan_id            INT NOT NULL PRIMARY KEY,
    date_id            INT NOT NULL,
    line_id            INT NOT NULL,
    product_id         INT NOT NULL,
    planned_good_units INT NOT NULL,                -- план придатних виробів, шт.
    UNIQUE (date_id, line_id, product_id),
    FOREIGN KEY (date_id)    REFERENCES dim_date(date_id),
    FOREIGN KEY (line_id)    REFERENCES production_lines(line_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
GO

-- work_orders: виробничі замовлення
CREATE TABLE work_orders (
    work_order_id INT NOT NULL PRIMARY KEY,
    plan_id       INT NOT NULL,
    date_id       INT NOT NULL,
    line_id       INT NOT NULL,
    product_id    INT NOT NULL,
    qty_ordered   INT NOT NULL,                     -- скільки треба запустити (з запасом на брак)
    FOREIGN KEY (plan_id)    REFERENCES production_plan(plan_id),
    FOREIGN KEY (date_id)    REFERENCES dim_date(date_id),
    FOREIGN KEY (line_id)    REFERENCES production_lines(line_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
GO

-- batches: партії по 50 штук
CREATE TABLE batches (
    batch_id      INT NOT NULL PRIMARY KEY,
    work_order_id INT NOT NULL,
    shift_id      INT NOT NULL,
    qty_planned   INT NOT NULL,                     -- мали запустити
    qty_started   INT NOT NULL,                     -- запустили фактично (після простоїв)
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id),
    FOREIGN KEY (shift_id)      REFERENCES shifts(shift_id)
);
GO

-- units: окремі вироби. 1 рядок = 1 пристрій
CREATE TABLE units (
    unit_id              INT         NOT NULL PRIMARY KEY,   -- серійний номер
    batch_id             INT         NOT NULL,
    scrapped_at_stage_id INT         NULL,                   -- етап списання, для Good пусто
    final_status         VARCHAR(10) NOT NULL,               -- Good або Rejected
    CHECK (final_status IN ('Good', 'Rejected')),
    FOREIGN KEY (batch_id)             REFERENCES batches(batch_id),
    FOREIGN KEY (scrapped_at_stage_id) REFERENCES production_stages(stage_id)
);
GO

-- test_results: спроби тестування. 1 рядок = 1 спроба
CREATE TABLE test_results (
    test_id        INT        NOT NULL PRIMARY KEY,
    unit_id        INT        NOT NULL,
    attempt_no     INT        NOT NULL,                      -- 1, 2 або 3
    date_id        INT        NOT NULL,
    result         VARCHAR(4) NOT NULL,                      -- Pass або Fail
    defect_type_id INT        NULL,                          -- для Pass пусто
    CHECK (attempt_no BETWEEN 1 AND 3),
    CHECK (result IN ('Pass', 'Fail')),
    UNIQUE (unit_id, attempt_no),                            -- без двох однакових спроб
    FOREIGN KEY (unit_id)        REFERENCES units(unit_id),
    FOREIGN KEY (date_id)        REFERENCES dim_date(date_id),
    FOREIGN KEY (defect_type_id) REFERENCES defect_types(defect_type_id)
);
GO

-- quality_inspections: інспекції якості
CREATE TABLE quality_inspections (
    inspection_id  INT         NOT NULL PRIMARY KEY,
    unit_id        INT         NOT NULL,
    date_id        INT         NOT NULL,
    stage_id       INT         NOT NULL,
    defect_type_id INT         NOT NULL,
    result         VARCHAR(10) NOT NULL,                     -- Fail або Reworked
    CHECK (result IN ('Fail', 'Reworked')),
    UNIQUE (unit_id),                                        -- одна інспекція на виріб
    FOREIGN KEY (unit_id)        REFERENCES units(unit_id),
    FOREIGN KEY (date_id)        REFERENCES dim_date(date_id),
    FOREIGN KEY (stage_id)       REFERENCES production_stages(stage_id),
    FOREIGN KEY (defect_type_id) REFERENCES defect_types(defect_type_id)
);
GO

-- downtime_records: простої ліній
CREATE TABLE downtime_records (
    downtime_id  INT NOT NULL PRIMARY KEY,
    date_id      INT NOT NULL,
    line_id      INT NOT NULL,
    shift_id     INT NOT NULL,
    reason_id    INT NOT NULL,
    duration_min INT NOT NULL,                               -- тривалість, хвилин
    CHECK (duration_min > 0),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id),
    FOREIGN KEY (line_id)   REFERENCES production_lines(line_id),
    FOREIGN KEY (shift_id)  REFERENCES shifts(shift_id),
    FOREIGN KEY (reason_id) REFERENCES downtime_reasons(reason_id)
);
GO

-- production_costs: витрати. 1 рядок = день x лінія x продукт
CREATE TABLE production_costs (
    cost_id       INT           NOT NULL PRIMARY KEY,
    date_id       INT           NOT NULL,
    line_id       INT           NOT NULL,
    product_id    INT           NOT NULL,
    units_started INT           NOT NULL,
    material_cost DECIMAL(14,2) NOT NULL,
    labor_cost    DECIMAL(14,2) NOT NULL,
    overhead_cost DECIMAL(14,2) NOT NULL,
    total_cost    DECIMAL(14,2) NOT NULL,
    UNIQUE (date_id, line_id, product_id),
    FOREIGN KEY (date_id)    REFERENCES dim_date(date_id),
    FOREIGN KEY (line_id)    REFERENCES production_lines(line_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
GO