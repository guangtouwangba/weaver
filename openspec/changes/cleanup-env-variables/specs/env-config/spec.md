# Environment Configuration Specification

## Overview

定义项目环境变量配置的规范，确保 env.example 文件与实际代码保持同步。

## REMOVED Requirements

### Requirement: Unused database pool configuration

数据库连接池配置变量 MUST 从 env.example 移除，因为代码中未使用。

#### Scenario: Database pool variables removed

**Given** 后端 env.example 文件
**When** 查看数据库配置部分
**Then** SHALL NOT 包含 `DB_POOL_SIZE` 变量
**And** SHALL NOT 包含 `DB_MAX_OVERFLOW` 变量

### Requirement: Unused LLM provider configuration

未使用的 LLM 提供商配置变量 MUST 从 env.example 移除。

#### Scenario: LLM provider variables removed

**Given** 后端 env.example 文件
**When** 查看 LLM 配置部分
**Then** SHALL NOT 包含 `LLM_PROVIDER` 变量
**And** SHALL NOT 包含 `LLM_TEMPERATURE` 变量
**And** SHALL NOT 包含 `LLM_MAX_TOKENS` 变量

### Requirement: Unused embedding configuration

未使用的 Embedding 配置变量 MUST 从 env.example 移除。

#### Scenario: Embedding variables removed

**Given** 后端 env.example 文件
**When** 查看 Embedding 配置部分
**Then** SHALL NOT 包含 `EMBEDDING_PROVIDER` 变量
**And** SHALL NOT 包含 `EMBEDDING_DIMENSIONS` 变量
**And** SHALL NOT 包含 `FAKE_EMBEDDING_SIZE` 变量

### Requirement: Unused OpenRouter site information

未使用的 OpenRouter 站点信息变量 MUST 从 env.example 移除。

#### Scenario: OpenRouter site variables removed

**Given** 后端 env.example 文件
**When** 查看 OpenRouter 配置部分
**Then** SHALL NOT 包含 `OPENROUTER_SITE_URL` 变量
**And** SHALL NOT 包含 `OPENROUTER_SITE_NAME` 变量

### Requirement: Unused runtime evaluation configuration

未使用的运行时评估配置变量 MUST 从 env.example 移除。

#### Scenario: Runtime evaluation variables removed

**Given** 后端 env.example 文件
**When** 查看评估配置部分
**Then** SHALL NOT 包含 `RUNTIME_EVALUATION_ENABLED` 变量
**And** SHALL NOT 包含 `RUNTIME_EVALUATION_MODE` 变量
**And** SHALL NOT 包含 `RUNTIME_EVALUATION_SAMPLING_RATE` 变量
**And** SHALL NOT 包含 `RUNTIME_EVALUATION_METRICS` 变量
**And** SHALL NOT 包含 `RUNTIME_EVALUATION_STORAGE_DIR` 变量
**And** SHALL NOT 包含 `RUNTIME_EVALUATION_SAVE_RESULTS` 变量

## MODIFIED Requirements

### Requirement: Synchronized env.example with config.py

env.example 文件 MUST 与 config.py 中的实际配置保持同步。

#### Scenario: All env.example variables have corresponding config

**Given** 后端 env.example 文件中定义的所有变量
**When** 在 config.py 的 Settings 类中查找对应属性
**Then** 每个环境变量 SHALL 有对应的 Settings 属性
**Or** 该变量应从 env.example 中移除
