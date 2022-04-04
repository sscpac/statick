# Metrics for Software Quality Assurance

- [Metrics for Software Quality Assurance](#metrics-for-software-quality-assurance)
  - [Summary](#summary)
  - [Code Quality Guidelines](#code-quality-guidelines)
  - [Effectiveness of Code Quality Approaches](#effectiveness-of-code-quality-approaches)
  - [Tools](#tools)
  - [Best Practices](#best-practices)
  - [Unsorted](#unsorted)

## Summary

This is a literature survey of metrics used to determine the quality of software.
Each paper will have a summary of metrics, the correlation of metrics to software quality,
definitions of quality, and a list of any available tools to generate the metrics.
Note that not all papers will include each of those features.

Some of the ways that quality is used:

- Fault detection
- Maintainability
- Extensibility
- Security

## Code Quality Guidelines

**CMU SEI CERT C++ Coding Standard** \
2016 \
<https://wiki.sei.cmu.edu/confluence/display/cplusplus/CC.+Analyzers>

This is a set of rules and recommendations for writing secure code.
The nice thing is that for each guideline the authors have identified static analysis tools and their
respective flags that can be used to identify violations of the guidelines.
There are examples showing violations and how to fix them.

The open source tools they identify are: clang-tidy, cppcheck, findbugs, Make.
Using these open source tools makes it straightforward to verify that a subset of the recommended standards
are being applied to a particular code base.

Statick has a specific configuration to use these open source tools with the flags recommended by this standard.
Statick also extends the recommended tools to identify the same types of security issues for languages other than C++.

**Software Quality Metrics for Object-Oriented Environments** \
Dr. Linda H. Rosenberg and Lawrence E. Hyatt \
Goddard Space Flight Center \
<https://pdfs.semanticscholar.org/fc8c/16be91c43bb15b72e2c73728839c1a9468ef.pdf> \
<https://people.ucalgary.ca/~far/Lectures/SENG421/PDF/oocross.pdf>

The authors identify five attributes that contribute to quality software: efficiency, complexity,
understandability, reusability, testability/maintainability.

They then identify ways to measure features of software and tie those features back to the software quality attributes.
The features they use are: cyclomatic complexity, size, comment percentage, weighted methods per class,
response for a class (similar to afferent coupling), lack of cohesion of methods, coupling between object
classes, depth of inheritance tree, number of children.

The CCCC static analysis tool is capable of measuring most of the metrics identified.
The main missing metric is lack of cohesion of methods.

**MISRA-C** \
<https://www.misra.org.uk/Activities/MISRAAutocode/tabid/72/Default.aspx>

**AUTOSAR** \
<https://www.autosar.org/fileadmin/user_upload/standards/adaptive/17-03/AUTOSAR_RS_CPP14Guidelines.pdf>

**OWASP** \
<https://www.owasp.org/index.php/Main_Page>

## Effectiveness of Code Quality Approaches

**Principal Components of Orthogonal Object-Oriented Metrics** \
Victor Laing And Charles Coleman \
NASA Software Assurance Technology Center \
2001 \
<https://pdfs.semanticscholar.org/1026/0d67fa5ed4ecea9dd4398c3f236c52cabf6b.pdf>

The authors start by saying that software quality can be derived from running a large set of static analysis
tools against source code and evaluating the results.
Then they attempt to determine if a subset of the tools and flags per tool can give comparable results in
measuring software quality.
If the subset approach is comparable to the full set it can save a significant amount of time to perform
the analysis and give feedback to developers.

The authors find that they are able to identify a subset of tools and flags to measure software quality.
They recommend running this subset for rapid feedback to developers, and then running a full analysis on
a nightly or weekly basis.

This group uses the Chidamber and Kemerer (CK) suite of metrics as the superset.
They provide an equation that uses the CK metrics to define software quality.
It would be good to identify open source tools that provide the CK metrics.
A description of the CK metrics, and some example values relating those metrics to software quality based on
this paper, is available in a separate resource from this survey:
"Chidamber and Kemerer object-oriented metrics suite".

**Predicting Faults from Cached History** \
Sunghun Kim and Thomas Zimmermann and E. James Whitehead, Jr. and Andreas Zeller \
MIT and Saarland University and UC Santa Cruz \
2008 \
<http://web.cs.ucdavis.edu/~devanbu/teaching/289/Schedule_files/Kim-Predicting.pdf>

The authors demonstrate success in identifying files and methods that are likely to contain faults.
They do this on seven open source projects that have a large history (more than 200,000 commits) and that have
tracked the identification and resolution of faults.
The method they use makes the assumption that faults do not happen independently, but instead are more likely
to be found in the same localities within the code (same files, same methods).

The benefit of identifying where faults are likely to occur is that more targeted review can
be applied to those files and methods.
This includes allocation of resources for peer review, writing unit tests, and possibly refactoring.

**Static Analysis Tools as Early Indicators of Pre-Release Defect Density** \
Nachiappan Nagappan and Thomas Ball \
North Carolina State University and Microsoft Research \
2005 \
<https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/icse05exp.pdf>

This was a study done by Microsoft against Windows Server 2003 that looked at using static analysis tools
to predict defects prior to release.
They found a strong positive correlation between defects identified by static analysis tools and defects found by testing.
Discriminant analysis also found that the defect density predicted by static analysis testing was strongly
correlated with high statistical significance with the actual defect density.
The study further found that static analysis defect density can be used to discriminate between components
of high and low quality.

The static analysis tools used are proprietary Microsoft products named PREfix and PREfast.
Examples of the types of faults these tools identify are NULL pointer dereferences, uninitialized variables,
the use of uninitialized memory, and double freeing of resources.
Since the tools are proprietary there is no way to get an exact match, but those types of faults can be
identified using open source static analysis tools.
I think it is reasonable to expect that a suite of well written open source tools, with appropriate flags
enabled, can also be used to predict defects.
As the authors point out, the ability to identify faults is highly dependent on the quality of the
static analysis tools used.

An additional observation was that using multiple static analysis tools improved the ability to predict faults.

**The Influence of Organizational Structure on Software Quality: An Empirical Case Study** \
Nachiappan Nagappan and Brendan Murphy and Victor R. Basili \
Microsoft Research, University of Maryland \
2008 \
<https://www.cs.umd.edu/~basili/publications/proceedings/P125.pdf>

This study found that organizational structure was a significantly better predictor of fault detection
than traditional metrics such as churn, complexity, coverage, and dependencies.
The authors describe the following metrics that are used to define organizational structure:

> For the organizational metrics, we try to capture issues such as organizational distance of the developers;
> the number of developers working on a component; the amount of multi-tasking developers are doing across
> organizations; and the amount of change to a component within the context of that organization etc.
> from a quantifiable perspective.

It is interesting to try to identify ways to measure these qualities in globally distributed development
environments without a central authority (such as ROS).

**Code coverage and postrelease defects: A largescale study on open source projects** \
Pavneet Singh Kochhar and David Lo and Julia Lawall and Nachiappan Nagappan \
Singapore Management University \
2017 \
<https://ink.library.smu.edu.sg/sis_research/3838/> \
<https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?referer=https://scholar.google.com/&httpsredir=1&article=4840&context=sis_research>

**On the Value of Static Analysis for Fault Detection in Software** \
Jiang Zheng and Laurie Williams and Nachiappan Nagappan and Will Snipes and John P. Hudepohl and Mladen A. Vouk \
North Carolina State University and Microsoft Research and Nortel Networks \
2006 \
<https://collaboration.csc.ncsu.edu/laurie/Papers/TSE-0197-0705-2.pdf>

**Coupling and Cohesion Measures in Object Oriented Programming** \
Mr. Kailash Patidar and Prof.Ravindra Kumar Gupta and Prof.Gajendra Singh Chandel \
SSSIST SEHORE \
2013 \
<https://pdfs.semanticscholar.org/6ea3/74521188b138c93a2d682d52ae986721ab66.pdf>

**Significance of Different Software Metrics in Defect Prediction** \
Marian Jureczko \
Wrocław University of Technology, Poland \
2011 \
<https://pdfs.semanticscholar.org/e848/d79d1f9c42b69cb902399287f67bb3ee0436.pdf>

**An Empirical Validation of Object Oriented Design Quality Metrics** \
R. A. Khan and K. Mustafa and S. I. Ahson \
JMI New Delhi, India \
2007 \
<https://www.sciencedirect.com/science/article/pii/S1319157807800012>

**Don’t Touch My Code! Examining the Effects of Ownership on Software Quality** \
Christian Bird and Nachiappan Nagappan and Brendan Murphy and Harald Gall and Premkumar Devanbu \
Microsoft Research, University of Zurich, UC Davis \
2011 \
<https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bird2011dtm.pdf>

**Use of Relative Code Churn Measures to Predict System Defect Density** \
Nachiappan Nagappan and Thomas Ball \
North Carolina State University and Microsoft Research \
2005 \
<http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.85.7712&rep=rep1&type=pdf>

**A Novel Machine Learning Approach for Bug Prediction** \
Shruthi Puranik and Pranav Deshpande and K. Chandrasekaran \
National Institute of Technology, Karnataka \
2016 \
<https://www.sciencedirect.com/science/article/pii/S1877050916315174>

**Independent Extensible Systems - Software Engineering Potential and Challenges** \
Clemens Szyperski \
Queensland University of Technology \
1996 \
<http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.56.5751&rep=rep1&type=pdf>

This paper was found from discussion at <https://www.quora.com/What-are-good-ways-to-measure-extensibility>.

The author finds that a system is independently extensible if new extensions can be safely added
without performing a global integrity check (without having global knowledge of the entire system).
“We call a system independently extensible, if it can cope with the late addition of extensions
without requiring a global integrity check.”

## Tools

**Chidamber and Kemerer object-oriented metrics suite** \
Project Analyzer Software Package \
<http://www.aivosto.com/project/help/pm-oo-ck.html>

The Chidamber and Kemerer metrics suite originally consists of 6 metrics calculated for each class:
weighted methods per class (WMC), depth of inheritance tree (DIT), number of children (NOC),
coupling between object classes (CBO), response for a class (RFC), and lack of cohesion of methods (LCOM1).
The original suite has later been amended by RFC, LCOM2, LCOM3 and LCOM4 by other authors.
Most of these metrics can be identified using the CCCC tool.

Example values for these metrics were found in a study done by NASA in a paper also found in this survey,
Principal Components of Orthogonal Object-Oriented Metrics.
The metrics were associated with qualitative descriptions of the quality of each project after evaluation from software experts.

System Analyzed | Java | Java | C++
:-------------- | :--- | :--- | :--
Classes | 46 | 1000 | 1617
Lines | 50,000 | 300,000 | 500,000
Quality | “Low” | “High” | “Medium”
CBO | 2.48 | 1.25 | 2.09
LCOM1 | 447.65 | 78.34 | 113.94
RFC | 80.39 | 43.84 | 28.60
NOC | 0.07 | 0.35 | 0.39
DIT | 0.37 | 0.97 | 1.02
WMC | 45.7 | 11.10 | 23.97

**Open Source Quality Measurements** \
Department of Software Engineering, University of Szeged \
2014 \
<http://www.inf.u-szeged.hu/projectdirs/osqm/>

## Best Practices

**Linux Foundation Core Infrastructure Initiative**
The Linux Foundation has the Core Infrastructure Initiative that is dedicated to making
open source software more secure and functional.
There is a CII Best Practices badge available for projects that follow the guidelines described at <https://bestpractices.coreinfrastructure.org/en>.
These best practices focus on code, results, organizational structure, and testing, among other criteria.

**Code Complete** \
Steve McConnell \
Chapter 5, Design in Construction

This book argues that the main goal of writing code is to manage complexity.
The section “Desirable Characteristics of a Design” lists high level goals that, if achieved,
will result in high quality software.
Some of the goals can be defined as metrics identified with static analysis tools.

The goals include: minimal complexity, ease of maintenance, loose coupling, extensibility, reusability,
high fan-in, low-to-medium fan-out, portability, leanness, stratification, standard techniques.
It is noted that some of these goals contradict each other and part of the challenge of creating software
is to evaluate the trade-offs associated with choices made with regards to these goals.

From <https://blog.codinghorror.com/code-reviews-just-do-it/>,
Steve McConnell identifies the following benefits of code review:

> … software testing alone has limited effectiveness – the average defect detection rate
> is only 25 percent for unit testing, 35 percent for function testing, and 45 percent for integration testing.
> In contrast, the average effectiveness of design and code inspections are 55 and 60 percent.
> Case studies of review results have been impressive:
>
> - In a software-maintenance organization, 55 percent of one-line maintenance changes were in error
>   before code reviews were introduced.
>   After reviews were introduced, only 2 percent of the changes were in error.
>   When all changes were considered, 95 percent were correct the first time after reviews were introduced.
>   Before reviews were introduced, under 20 percent were correct the first time.
> - In a group of 11 programs developed by the same group of people, the first 5 were developed without reviews.
>   The remaining 6 were developed with reviews.
>   After all the programs were released to production, the first 5 had an average of 4.5 errors per 100 lines of code.
>   The 6 that had been inspected had an average of only 0.82 errors per 100.
>   Reviews cut the errors by over 80 percent.
> - The Aetna Insurance Company found 82 percent of the errors in a program by using inspections and was
>   able to decrease its development resources by 20 percent.
> - IBM's 500,000 line Orbit project used 11 levels of inspections.
>   It was delivered early and had only about 1 percent of the errors that would normally be expected.
> - A study of an organization at AT&T with more than 200 people reported a 14 percent increase in productivity
>   and a 90 percent decrease in defects after the organization introduced reviews.
> - Jet Propulsion Laboratories estimates that it saves about $25,000 per inspection by finding
>   and fixing defects at an early stage.

**The Protection of Information in Computer Systems** \
Jerome H. Saltzer and Michael D. Schroeder \
MIT \
1975 \
<http://web.mit.edu/Saltzer/www/publications/protection/>

**The Pragmatic Programmer** \
Andy Hunt and Dave Thomas

**Clean Code** \
Robert Cecil Martin

**The Art of Giving and Receiving Code Reviews** \
Alex Hill \
2018 \
<http://www.alexandra-hill.com/2018/06/25/the-art-of-giving-and-receiving-code-reviews/>

## Unsorted

**Predicting Faults from Cached History** \
Sunghun Kim and Thomas Zimmermann and E. James Whitehead, Jr. and Andreas Zeller \
MIT, Saarland University, UC Santa Cruz \
2007 \
<https://web.cs.ucdavis.edu/~devanbu/teaching/289/Schedule_files/Kim-Predicting.pdf>

**On the Impact of Programming Languages on Code Quality** \
Emery D. Berger and Celeste Hollenbeck and Petr Maj and Olga Vitek and Jan Vitek \
University of Massachusetts Amherst, Northeastern University, Czech Technical University in Prague \
2019 \
<https://arxiv.org/pdf/1901.10220.pdf>

**Effects of Test-Driven Development: A Comparative Analysis of Empirical Studies** \
Simo Mäkinen and Jürgen Münch \
University of Helsinki \
2014 \
<https://helda.helsinki.fi/bitstream/handle/10138/42741/2014_01_swqd_author_version.pdf?sequence=2>

**Analyzing The Effects of Test Driven Development In GitHub** \
Neil C. Borle and Meysam Feghhi and Eleni Stroulia and Russell Greiner and Abram Hindle \
University of Alberta \
2018 \
<http://softwareprocess.es/pubs/borle2017EMSE-TDD.pdf>

**Need for Sleep: the Impact of a Night of Sleep Deprivation on Novice Developers’ Performance** \
Davide Fucci and Giuseppe Scanniello and Simone Romano, and Natalia Juristo \
University of Hamburg \
2018 \
<https://arxiv.org/pdf/1805.02544.pdf>

**Sleep Deprivation: Impact on cognitive performance** \
Paula Alhola and Päivi Polo-Kantola \
University of Turku \
2007 \
<https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2656292/>

**Scheduled Overtime Effect on Construction Projects** \
A Construction Industry Cost Effectiveness Task Force Report \
1980 \
<http://web.archive.org/web/20090824001133/http://www.curt.org/pdf/156.pdf>

**Happy software developers solve problems better: psychological measurements in empirical software engineering** \
Daniel Graziotin​ and Xiaofeng Wang and Pekka Abrahamsson \
Free University of Bozen-Bolzano \
2014 \
<https://peerj.com/articles/289/>

**A Systematic Literature Review on Fault Prediction Performance in Software Engineering** \
Tracy Hall and Sarah Beecham and David Bowes and David Gray and Steve Counsell \
Brunel University, University of Limerick, University of Hertfordshire \
2012 \
<https://ulir.ul.ie/bitstream/handle/10344/1772/2011_hall%20%28a%29.pdf?sequence=2> \

**Empirical Analysis of CK Metrics for Object-Oriented Design Complexity: Implications for Software Defects** \
Ramanath Subramanyam and M.S. Krishnan \
2003 \
<https://maisqual.squoring.com/wiki/images/4/4f/Subramanyam_krishnan.pdf>
