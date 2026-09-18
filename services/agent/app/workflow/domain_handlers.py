from ..domain_agents import project_schedule, schedule_variance, parse_ifc_summary, water_kpis, aeration_recommendation, telemetry_summary, alarm_rules

def handlers():
    def project_writeback(c):
        return {'type':'project.gantt.change_set','dry_run':True,'task_ids':c.get('task_ids',[]),'changes':c.get('changes',[])}
    def bim_issue(c):
        return {'type':'bim.issue','created':True,'severity':c.get('severity','medium'),'title':c.get('title','BIM issue'),'element_ids':c.get('element_ids',[])}
    def work_order(c):
        return {'type':'work_order','created':True,'system':c.get('system','generic'),'title':c.get('title','Agent work order'),'priority':c.get('priority','normal')}
    def scada_proposal(c):
        return {'type':'scada.control.proposal','executed':False,'approval_required':True,'point':c.get('point'),'value':c.get('value')}
    return {
        'project.schedule': lambda c: {'items': project_schedule(c.get('tasks', []))},
        'project.variance': lambda c: schedule_variance(c['planned_finish'], c.get('actual_finish'), c.get('today')),
        'project.gantt.writeback': project_writeback,
        'bim.ifc.summary': lambda c: parse_ifc_summary(c['content']),
        'bim.issue.create': bim_issue,
        'water.kpi': lambda c: {'kpis':water_kpis(c.get('samples',[])), 'aeration':aeration_recommendation(c.get('samples',[]),c.get('target_do',2.0))},
        'iot.telemetry': lambda c: {'items':telemetry_summary(c.get('points',[])), 'alarms':alarm_rules(c.get('points',[]),c.get('high'),c.get('low'))},
        'iot.work_order.create': work_order,
        'scada.control.proposal': scada_proposal,
    }
