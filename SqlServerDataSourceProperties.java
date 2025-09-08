package com.taishinlife.nxs.teplapi.config;

import lombok.Data;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Data
@Component
public class SqlServerDataSourceProperties {

    @Value("${primary.datasource.url}")
    private String dataSourceUrl;
    @Value("${primary.datasource.dbusername}")
    private String username;
    @Value("${primary.datasource.password}")
    private String mima;
    @Value("${primary.datasource.driver-class-name}")
    private String driverClassName;
}
