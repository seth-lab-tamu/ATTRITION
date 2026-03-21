##c6288 c7552 s13207 s15850 mips aes_final gps_final mor1kx_final
for v in c5315 c6288 c7552
do
export v_file=$v
export technique=DETERRENT # detection technique: random_LT or MERO or GA_SAT or TARMAC or TGRL or TMAX or DETERRENT_for_AI_vs_Humans_CSAW22
export trojan_source=random #RL # trojan source: random or RL or heuristic or evading_TMAX
export trigger_width=4  # 4 or sometimes 6,8,10
python -u testing_pats_analysis.py | tee $v_file\_$trojan_source\_$trigger_width\_width_Trojans_$technique\_test_patterns.txt
#python testing_pats_analysis.py
#echo $v_file\_$trojan_source\_$trigger_width\_width_Trojans_$technique\_test_patterns done
printf "${v_file}_${trojan_source}_${trigger_width}_width_Trojans_${technique}_test_patterns done \n\n"
done

# For GLSVLSI netlists
#for v in c1355_GLSVLSI
#do
#export v_file=$v
#export technique=TARMAC # detection technique: random_LT or MERO or GA_SAT or TARMAC or TGRL
#export trojan_source=random #GLSVLSI #RL # trojan source: random or RL or heuristic or GLSVLSI
##export trigger_width=4  # 4 or sometimes 6,8,10
#python -u testing_pats_analysis_GLSVLSI.py | tee $v_file\_$trojan_source\_all_width_Trojans_$technique\_test_patterns.txt
##python testing_pats_analysis.py
##echo $v_file\_$trojan_source\_$trigger_width\_width_Trojans_$technique\_test_patterns done
#printf "${v_file}_${trojan_source}_${trigger_width}_width_Trojans_${technique}_test_patterns done \n\n"
#done