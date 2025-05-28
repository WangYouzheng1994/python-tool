CREATE TABLE `maintenance_deploy_config` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `service_name` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务名称',
  `service_code` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务号',
  `instance_no` int DEFAULT NULL COMMENT '实例号',
  `ip` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'ip',
  `port` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '端口',
  `deploy_file_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '部署地址',
  `service_type` varchar(15) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '1:java;2:前端vue2',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `create_by` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建人',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '上次修改时间',
  `del_flag` tinyint NOT NULL DEFAULT '0' COMMENT '是否删除(0 未删除  1已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_service_instance` (`service_code`,`instance_no`) COMMENT '服务+实例唯一'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='运维中心，部署机器清单';