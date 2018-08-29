import shlex, subprocess


#cwl_file = "https://github.com/elixir-europe/WES-ELIXIR/blob/7d6e4084d18fdd7d31252191e012bf75ef57bb06/tests/cwl/echo-job.yml"
cwl_file = "cwl/echo-job.yml"

command = "cwl-tes --tes https://tes-dev.tsi.ebi.ac.uk/ " + cwl_file + " --message \"Hello from Basel\""

print(command)

command_args = shlex.split(command)

print(command_args)

subprocess.run(command_args)
