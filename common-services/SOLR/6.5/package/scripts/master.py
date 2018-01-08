import sys, os, pwd, grp, signal, time
from resource_management import *
from subprocess import call

class Master(Script):

  #Call setup_solr.sh to install the service
  def install(self, env):

    #import properties defined in -config.xml file from params class
    import params
    import status_params

    # Install packages listed in metainfo.xml
    self.install_packages(env)

    try: grp.getgrnam(params.solr_group)
    except KeyError: Group(group_name=params.solr_group)

    try: pwd.getpwnam(params.solr_user)
    except KeyError: User(username=params.solr_user,
                          gid=params.solr_group,
                          groups=[params.solr_group],
                          ignore_failures=True)

    Directory([params.solr_log_dir, status_params.solr_piddir, params.solr_dir],
              mode=0755,
              cd_access='a',
              owner=params.solr_user,
              group=params.solr_group,
              recursive=True
          )


    File(params.solr_log,
            mode=0644,
            owner=params.solr_user,
            group=params.solr_group,
            content=''
    )

    Execute('echo Solr dir: ' + params.solr_dir)

    if params.solr_bindir == 'UNDEFINED' or params.cloud_scripts == 'UNDEFINED':
      Execute('echo Error: solr_bin: ' + params.solr_bindir + ' cloud_scripts: ' + params.cloud_scripts)

    Directory([params.solr_conf, params.solr_datadir, params.solr_data_resources_dir],
              mode=0755,
              cd_access='a',
              owner=params.solr_user,
              group=params.solr_group,
              recursive=True
          )

    Execute ('echo "Solr install complete"')



  def configure(self, env):
    import params
    env.set_params(params)

    #write content in jinja text field to solr-env.sh
    env_content=InlineTemplate(params.solr_env_content)
    File(format("{solr_conf}/solr-env.sh"), content=env_content, owner=params.solr_user)

    
    xml_content=InlineTemplate(params.solr_xml_content)    
    File(format("{solr_datadir}/solr.xml"), content=xml_content, owner=params.solr_user)    

    log4j_content=InlineTemplate(params.solr_log4j_content)    
    File(format("{solr_datadir}/resources/log4j.properties"), content=log4j_content, owner=params.solr_user)    

    zoo_content=InlineTemplate(params.solr_zoo_content)    
    File(format("{solr_datadir}/zoo.cfg"), content=zoo_content, owner=params.solr_user)    

      

  #Call start.sh to start the service
  def start(self, env):

    #import properties defined in -config.xml file from params class
    import params

    #import status properties defined in -env.xml file from status_params class
    import status_params
    self.configure(env)

    #this allows us to access the params.solr_pidfile property as format('{solr_pidfile}')
    env.set_params(params)

    #form command to invoke setup_solr.sh with its arguments and execute it
    cmd = format("{service_packagedir}/scripts/setup_solr.sh {solr_dir} {solr_user} >> {solr_log} 2>&1")
    Execute('echo "Running ' + cmd + '" as root')
    Execute(cmd, ignore_failures=True)


    #form command to invoke start.sh with its arguments and execute it
    if params.solr_cloudmode:
      Execute ('echo "Creating znode" ' + params.solr_znode)
      Execute ('echo "' + params.cloud_scripts + '/zkcli.sh -zkhost ' + params.zookeeper_hosts + ' -cmd makepath ' + params.solr_znode + '"')
      Execute (format("export JAVA_HOME={java64_home};{cloud_scripts}/zkcli.sh -zkhost {zookeeper_hosts} -cmd makepath {solr_znode}"), user=params.solr_user, ignore_failures=True)

      Execute(format('SOLR_INCLUDE={solr_conf}/solr-env.sh {solr_bindir}/solr start -cloud -noprompt -s {solr_datadir} >> {solr_log} 2>&1'), user=params.solr_user)

      if params.create_ranger_audit:
        Execute(format('SOLR_INCLUDE={solr_conf}/solr-env.sh {solr_bindir}/solr create -c ranger_audits -d data_driven_schema_configs -s 1 -rf 1 >> {solr_log} 2>&1'), user=params.solr_user, ignore_failures=True)

    else:
      cmd = params.service_packagedir + '/scripts/start.sh ' + params.solr_dir + ' ' + params.solr_log + ' ' + status_params.solr_pidfile + ' ' + params.solr_bindir
      Execute('echo "Running cmd: ' + cmd + '"')    
      Execute(cmd, user=params.solr_user)


  #Called to stop the service using the pidfile
  def stop(self, env):
    import params

    #import status properties defined in -env.xml file from status_params class  
    import status_params

    #this allows us to access the params.solr_pidfile property as format('{solr_pidfile}')
    env.set_params(params)
    #self.configure(env)


    #kill the instances of solr
    Execute (format('SOLR_INCLUDE={solr_conf}/solr-env.sh {solr_bindir}/solr stop -all >> {solr_log}'), user=params.solr_user, ignore_failures=True)  

    #delete the pid file
    Execute (format("rm -f {solr_pidfile} >> {solr_log}"), user=params.solr_user, ignore_failures=True)

  #Called to get status of the service using the pidfile
  def status(self, env):

    #import status properties defined in -env.xml file from status_params class
    import status_params
    env.set_params(status_params)

    #use built-in method to check status using pidfile
    check_process_status(status_params.solr_pidfile)



if __name__ == "__main__":
  Master().execute()
