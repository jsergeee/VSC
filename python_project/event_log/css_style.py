#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSS стили для HTML отчета
"""

CSS_STYLE = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #4a6491);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
        }
        
        .stat-card .label {
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card.critical .number {
            color: #e74c3c;
        }
        
        .cve-section {
            padding: 30px;
            background: #fff3cd;
            border-left: 4px solid #f39c12;
            margin: 20px 30px;
            border-radius: 5px;
        }
        
        .cve-section h2 {
            color: #856404;
            margin-bottom: 15px;
        }
        
        .cve-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .cve-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .cve-id {
            font-size: 1.2em;
            font-weight: bold;
            color: #c0392b;
            margin-bottom: 5px;
        }
        
        .cve-desc {
            color: #555;
            margin-bottom: 10px;
        }
        
        .cve-severity {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            background: #e74c3c;
            color: white;
            margin-right: 5px;
        }
        
        .cve-remediation {
            font-size: 0.9em;
            color: #27ae60;
            margin-top: 10px;
        }
        
        .critical-events {
            padding: 0 30px 30px 30px;
        }
        
        .critical-events h2 {
            color: #c0392b;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e74c3c;
        }
        
        .critical-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .critical-item {
            background: #fdf2f2;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 20px;
        }
        
        .critical-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .critical-id {
            font-size: 1.3em;
            font-weight: bold;
            color: #721c24;
        }
        
        .critical-time {
            color: #856404;
            font-size: 0.9em;
        }
        
        .subjects-table {
            width: 100%;
            margin-top: 15px;
            border-collapse: collapse;
        }
        
        .subjects-table td {
            padding: 8px;
            border-bottom: 1px solid #f5c6cb;
        }
        
        .subjects-table td:first-child {
            font-weight: bold;
            width: 40%;
        }
        
        .top-events {
            padding: 0 30px 30px 30px;
        }
        
        .top-events h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        .top-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .top-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .top-item .event-id {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .top-item .event-desc {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .top-item .event-count {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .category-stats {
            padding: 30px;
            background: #f8f9fa;
        }
        
        .category-stats h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        .category-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .category-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .category-item.critical {
            border-left-color: #e74c3c;
        }
        
        .category-item h3 {
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .category-item p {
            color: #555;
        }
        
        .category-item .critical-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            background: #e74c3c;
            color: white;
            font-size: 0.8em;
            margin-left: 10px;
        }
        
        .events-table {
            padding: 30px;
            overflow-x: auto;
        }
        
        .events-table h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        th {
            background: #2c3e50;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            cursor: pointer;
        }
        
        th:hover {
            background: #34495e;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        tr:hover {
            background: #f5f7fa;
        }
        
        .event-id {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .count {
            text-align: center;
            font-weight: bold;
            border-radius: 20px;
            padding: 5px 10px;
            display: inline-block;
            min-width: 60px;
        }
        
        .count-0 { background: #ecf0f1; color: #7f8c8d; }
        .count-1 { background: #d5f4e6; color: #27ae60; }
        .count-low { background: #fff3cd; color: #856404; }
        .count-medium { background: #f8d7da; color: #721c24; }
        .count-high { background: #721c24; color: white; }
        
        .level-badge {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .cve-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            background: #c0392b;
            color: white;
            font-size: 0.7em;
            margin-right: 3px;
            margin-bottom: 3px;
        }
        
        .search-box {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .footer {
            background: #34495e;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }
        
        .highlight {
            background: yellow;
            padding: 2px;
            border-radius: 3px;
        }
        
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: help;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        
        /* НОВЫЕ СТИЛИ ДЛЯ РАСШИРЕННОГО АНАЛИЗА */
        .user-stats, .ip-stats, .privilege-stats, .time-analysis {
            padding: 30px;
            background: #f8f9fa;
            margin-top: 20px;
            border-top: 2px solid #e0e0e0;
        }
        
        .user-stats h2, .ip-stats h2, .privilege-stats h2, .time-analysis h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }
        
        .stats-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stats-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .stats-card h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #3498db;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .stats-card h3 i {
            font-size: 1.3em;
        }
        
        .stats-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .stats-list li {
            padding: 12px 0;
            border-bottom: 1px solid #ecf0f1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s ease;
        }
        
        .stats-list li:hover {
            background-color: #f8f9fa;
            padding-left: 10px;
        }
        
        .stats-list li:last-child {
            border-bottom: none;
        }
        
        .stats-list .user-name {
            font-weight: 500;
            color: #2c3e50;
            font-size: 0.95em;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .stats-list .user-count {
            background: #3498db;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            min-width: 50px;
            text-align: center;
        }
        
        .stats-list .failed-count {
            background: #e74c3c;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            min-width: 50px;
            text-align: center;
        }
        
        .logon-type-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-align: center;
        }
        
        .logon-type-2 { background: #2ecc71; color: white; }
        .logon-type-3 { background: #3498db; color: white; }
        .logon-type-4 { background: #9b59b6; color: white; }
        .logon-type-5 { background: #f1c40f; color: #2c3e50; }
        .logon-type-7 { background: #e67e22; color: white; }
        .logon-type-8 { background: #1abc9c; color: white; }
        .logon-type-9 { background: #e74c3c; color: white; }
        .logon-type-10 { background: #34495e; color: white; }
        .logon-type-11 { background: #7f8c8d; color: white; }
        
        .privilege-item {
            background: #f8f9fa;
            border-left: 4px solid;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
            transition: transform 0.2s ease;
        }
        
        .privilege-item:hover {
            transform: translateX(5px);
        }
        
        .privilege-high { border-left-color: #e74c3c; background: #fdf2f2; }
        .privilege-medium { border-left-color: #f39c12; background: #fff3e0; }
        
        .privilege-name {
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        
        .privilege-desc {
            font-size: 0.9em;
            color: #7f8c8d;
            margin: 8px 0;
            line-height: 1.4;
        }
        
        .privilege-risk {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .risk-high { 
            background: #e74c3c; 
            color: white;
        }
        .risk-medium { 
            background: #f39c12; 
            color: white;
        }
        
        .time-chart {
            display: flex;
            height: 250px;
            align-items: flex-end;
            gap: 3px;
            margin: 30px 0 20px 0;
            padding: 10px 0;
            background: linear-gradient(to bottom, transparent 0%, rgba(52, 152, 219, 0.05) 100%);
            border-radius: 10px;
        }
        
        .time-bar {
            flex: 1;
            background: linear-gradient(to top, #3498db, #9b59b6);
            min-height: 3px;
            border-radius: 4px 4px 0 0;
            position: relative;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .time-bar:hover {
            transform: scaleY(1.1);
            background: linear-gradient(to top, #2980b9, #8e44ad);
            z-index: 10;
        }
        
        .time-bar::after {
            content: attr(data-count);
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8em;
            color: #2c3e50;
            font-weight: bold;
            background: white;
            padding: 2px 6px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            opacity: 0;
            transition: opacity 0.3s ease;
            white-space: nowrap;
        }
        
        .time-bar:hover::after {
            opacity: 1;
        }
        
        .time-label {
            display: flex;
            justify-content: space-between;
            padding: 0 10px;
            font-size: 0.85em;
            color: #7f8c8d;
            font-weight: 500;
            margin-top: 10px;
        }
        
        .ip-address {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .ip-type {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: #ecf0f1;
            color: #7f8c8d;
        }
        
        .ip-private { 
            background: #f1c40f; 
            color: #2c3e50;
        }
        .ip-public { 
            background: #e74c3c; 
            color: white;
        }
        .ip-loopback { 
            background: #95a5a6; 
            color: white;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-style: italic;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        @media (max-width: 768px) {
            .summary {
                grid-template-columns: 1fr;
            }
            
            .category-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            th, td {
                padding: 10px;
                font-size: 14px;
            }
            
            .ip-address {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            
            .time-chart {
                height: 180px;
            }
        }
"""