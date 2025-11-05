ALTER TABLE task_readmes 
ADD COLUMN rendered_content LONGTEXT NULL COMMENT '渲染后的内容';

-- 为repositories表添加claude_session_id字段
ALTER TABLE repositories 
ADD COLUMN claude_session_id VARCHAR(255) NULL COMMENT 'Claude会话ID';